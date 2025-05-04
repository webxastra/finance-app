"""
AI Expense Categorization Service

This module integrates the AI expense categorization system with the Flask application.
It provides routes and functions for expense categorization, corrections, and model retraining.
"""

from flask import Blueprint, request, jsonify, current_app, json
from flask_login import login_required, current_user
from .categorizer import ExpenseCategorizer, CATEGORY_HIERARCHY
from .insights import ExpenseInsights
from .training_data import generate_detailed_training_data
from models.expense import Expense
from models.user import User
from db import db
import logging
from datetime import datetime
import traceback
import time
import numpy as np
import os
from utils.json_utils import safe_jsonify, NumpyJSONEncoder, convert_numpy_types
from models.ai_correction import AICorrection
from sqlalchemy.orm import scoped_session, sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
ai_expense = Blueprint('ai_expense', __name__, url_prefix='/api/ai')
# Configure blueprint to use custom encoder
ai_expense.json_encoder = NumpyJSONEncoder

# Global reference to the AI trainer instance
ai_trainer = None

def get_trainer():
    """Get or initialize the AI trainer instance"""
    global ai_trainer
    
    if ai_trainer is None:
        # Import here to avoid circular imports
        from .ai_trainer import AITrainer
        
        # Create base directory for AI data
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'ai')
        os.makedirs(base_dir, exist_ok=True)
        
        # Initialize trainer
        ai_trainer = AITrainer(base_dir=base_dir)
        
        # Initialize model if needed
        if not ai_trainer.classifier.is_trained:
            try:
                # Try to load existing model
                loaded = ai_trainer.classifier.load()
                
                # If no model exists, train initial model
                if not loaded:
                    logger.info("No existing model found, training initial model")
                    ai_trainer.train_initial_model()
            except Exception as e:
                logger.error(f"Error initializing AI model: {str(e)}")
                # Force training with default data as fallback
                try:
                    logger.info("Attempting to train model with default data as fallback")
                    ai_trainer.train_with_default_data()
                except Exception as train_e:
                    logger.error(f"Fallback training also failed: {str(train_e)}")
    
    # Ensure the model is trained
    if ai_trainer and not ai_trainer.classifier.is_trained:
        try:
            logger.info("Model not trained, training with default data")
            ai_trainer.train_with_default_data()
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
    
    return ai_trainer

# Function to safely train the model with retries
def safe_train_model(retries=3, delay=2):
    """Safely train the model with multiple retries"""
    global ai_trainer
    
    logger.info("Using fixed trainer implementation with dynamic test_size adjustments")
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Training attempt {attempt}/{retries} for expense categorization model")
            ai_trainer.train_with_default_data()
            logger.info("Successfully trained expense categorization model")
            return True
        except Exception as e:
            logger.error(f"Error training model (attempt {attempt}/{retries}): {str(e)}")
            logger.error(traceback.format_exc())
            
            if attempt < retries:
                logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
                # Increase delay for next retry (exponential backoff)
                delay *= 2
            else:
                logger.error(f"Failed to train model after {retries} attempts")
                return False

# Ensure the model is trained on startup
ai_trainer = get_trainer()
safe_train_model(retries=5, delay=3)

@ai_expense.route('/status', methods=['GET'])
@login_required
def model_status():
    """
    Check the status of the expense categorization model
    
    Returns:
    {
        "status": "ready" or "not_trained",
        "message": "Additional information about model status"
    }
    """
    try:
        # Check if the model is trained
        model_trained = ai_trainer.classifier.is_trained
        
        response = {
            "status": "ready" if model_trained else "not_trained",
            "message": "Model is ready to use" if model_trained else "Model needs training"
        }
        
        return safe_jsonify(response)
    
    except Exception as e:
        logger.error(f"Error checking model status: {str(e)}")
        return safe_jsonify({
            "status": "error",
            "message": f"Error checking model status: {str(e)}"
        }), 500

@ai_expense.route('/train-now', methods=['POST'])
@login_required
def train_now():
    """
    Force immediate training of the model with default data
    
    Returns:
    {
        "success": true/false,
        "message": "Success or error message"
    }
    """
    try:
        logger.info("Force-training model with default data")
        accuracy = ai_trainer.train_with_default_data()
        
        return safe_jsonify({
            "success": True,
            "message": "Successfully trained model",
            "accuracy": accuracy
        })
    
    except Exception as e:
        logger.error(f"Error force-training model: {str(e)}")
        logger.error(traceback.format_exc())
        return safe_jsonify({
            "success": False,
            "message": f"Error training model: {str(e)}"
        }), 500

@ai_expense.route('/categorize', methods=['POST'])
@login_required
def categorize_expense():
    """
    Categorize an expense based on its description
    
    Request JSON:
    {
        "description": "Expense description text",
        "amount": (optional) Expense amount
    }
    
    Returns:
        JSON with categorization results
    """
    try:
        # Ensure AI trainer is initialized
        global ai_trainer
        if ai_trainer is None:
            ai_trainer = get_trainer()
            
        # Get request data
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: description'
            }), 400
        
        description = data['description']
        amount = data.get('amount')  # Optional
        
        # Get trainer and make prediction
        trainer = get_trainer()
        prediction = trainer.predict_category(description, amount)
        
        if not prediction.get('success', False):
            return jsonify({
                'success': False,
                'message': 'Failed to categorize expense',
                'error': prediction.get('message', 'Unknown error')
            }), 500
        
        # Return prediction
        return jsonify({
            'success': True,
            'category': prediction['category'],
            'confidence': prediction['confidence'],
            'alternatives': prediction['alternatives'],
            'explanation': prediction['explanation'],
            'model_version': prediction['model_version']
        })
        
    except Exception as e:
        logger.error(f"Error categorizing expense: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ai_expense.route('/analyze', methods=['GET'])
@login_required
def analyze_insights():
    """
    Analyze user expenses and generate insights
    
    Query parameters:
    - days: Number of days to analyze (default 30)
    - limit: Maximum number of expenses to analyze (default 100)
    - types: Comma-separated list of insight types to generate
    
    Returns:
    {
        "insights": [
            {"type": "category_distribution", "message": "..."},
            ...
        ]
    }
    """
    try:
        # Get parameters
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))
        
        insight_types = request.args.get('types', 'all')
        if insight_types != 'all':
            insight_types = insight_types.split(',')
            
        # Import insights engine
        from .insights import InsightsEngine
        insights_engine = InsightsEngine()
        
        # Get user expenses
        from models import Expense
        from datetime import timedelta
        
        from_date = datetime.now() - timedelta(days=days)
        
        expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= from_date
        ).order_by(Expense.date.desc()).limit(limit).all()
        
        # Generate insights
        insights = insights_engine.generate_insights(
            expenses=expenses,
            user_data={'id': current_user.id},
            types=insight_types
        )
        
        return safe_jsonify({'insights': insights})
    
    except Exception as e:
        logger.error(f"Error in analyze_insights: {str(e)}")
        logger.error(traceback.format_exc())
        return safe_jsonify({'error': str(e)}), 500

@ai_expense.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """
    Get all available expense categories
    
    Query parameters:
    - detailed: Whether to return detailed subcategories (default false)
    
    Returns:
    {
        "categories": ["Category1", "Category2", ...],
        "hierarchy": {"MainCategory1": ["Sub1", "Sub2", ...], ...}
    }
    """
    try:
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        if detailed:
            return safe_jsonify({
                'categories': ai_trainer.classifier.categories + sum(CATEGORY_HIERARCHY.values(), []),
                'hierarchy': CATEGORY_HIERARCHY
            })
        else:
            return safe_jsonify({
                'categories': ai_trainer.classifier.categories,
                'hierarchy': CATEGORY_HIERARCHY
            })
    
    except Exception as e:
        logger.error(f"Error in get_categories: {str(e)}")
        return safe_jsonify({'error': str(e)}), 500

@ai_expense.route('/train', methods=['POST'])
@login_required
def train_categorizer():
    """
    Manually train the expense categorizer with user data
    Admin or user-specific training can be implemented here
    
    Request JSON:
    {
        "use_user_data": true/false,  # Whether to include user's data
        "use_detailed": true/false,   # Whether to train detailed categories
        "grid_search": true/false     # Whether to use grid search for hyperparameter tuning
    }
    
    Returns:
    {
        "success": true,
        "accuracy": 0.92,
        "message": "Model trained with 150 transactions"
    }
    """
    global ai_trainer
    try:
        # Get training parameters
        use_user_data = request.json.get('use_user_data', False)
        use_detailed = request.json.get('use_detailed', False)
        grid_search = request.json.get('grid_search', False)
        
        # Choose the appropriate categorizer
        active_categorizer = ai_trainer.classifier
        if use_detailed:
            if ai_trainer is None:
                ai_trainer = ExpenseCategorizer(use_detailed_categories=True)
            active_categorizer = ai_trainer
        
        # Training data and descriptions
        descriptions = []
        categories = []
        
        if use_user_data:
            # Get user's expenses with descriptions
            expenses = Expense.query.filter(
                Expense.user_id == current_user.id,
                Expense.description.isnot(None),
                Expense.description != ''
            ).all()
            
            if expenses and len(expenses) >= 10:
                # Extract descriptions and categories
                user_descriptions = [exp.description for exp in expenses]
                user_categories = [exp.category for exp in expenses]
                
                descriptions.extend(user_descriptions)
                categories.extend(user_categories)
                
                logger.info(f"Added {len(user_descriptions)} user transactions to training data")
        
        # Add default training data
        if use_detailed:
            # Get detailed training data (generated on demand)
            from .training_data import generate_detailed_training_data
            detailed_data = generate_detailed_training_data()
            descriptions.extend(detailed_data['descriptions'])
            categories.extend(detailed_data['categories'])
            logger.info(f"Added {len(detailed_data['descriptions'])} detailed default examples")
        else:
            # Get main category training data
            from .training_data import MAIN_CATEGORY_TRAINING_DATA
            default_descriptions = MAIN_CATEGORY_TRAINING_DATA['descriptions']
            default_categories = MAIN_CATEGORY_TRAINING_DATA['categories']
            descriptions.extend(default_descriptions)
            categories.extend(default_categories)
            logger.info(f"Added {len(default_descriptions)} default examples")
        
        # Train the model
        if len(descriptions) > 0:
            # Get accuracy metrics from training
            metrics = active_categorizer.train(descriptions, categories, grid_search=grid_search)
            
            # Convert any numpy values in accuracy metrics to Python native types
            processed_metrics = convert_numpy_types(metrics)
            
            return safe_jsonify({
                'success': True,
                'accuracy': processed_metrics.get('accuracy', 0.0),
                'precision': processed_metrics.get('precision', 0.0),
                'recall': processed_metrics.get('recall', 0.0),
                'f1_score': processed_metrics.get('f1_score', 0.0),
                'message': f'Model trained with {len(descriptions)} examples' + 
                           (', using grid search' if grid_search else '')
            })
        else:
            return safe_jsonify({
                'success': False,
                'message': 'No training data available'
            }), 400
        
    except Exception as e:
        logger.error(f"Error in train_categorizer: {str(e)}")
        logger.error(traceback.format_exc())
        return safe_jsonify({'error': str(e)}), 500

@ai_expense.route('/auto-categorize', methods=['POST'])
@login_required
def auto_categorize_expense():
    """
    Auto-categorize an expense and save to database
    
    Request JSON:
    {
        "description": "Transaction description",
        "amount": 50.00,
        "date": "2025-01-01",  # Optional, defaults to today
        "account_id": 1,  # Optional
        "notes": "Optional notes about the expense"
    }
    
    Returns:
    {
        "success": true,
        "expense_id": 123,
        "category": "Predicted Category",
        "confidence": 0.9
    }
    """
    try:
        global ai_trainer
        
        data = request.json
        
        if not data or 'description' not in data or 'amount' not in data:
            return safe_jsonify({
                'success': False,
                'message': 'Missing required parameters (description, amount)'
            }), 400
        
        description = data.get('description')
        amount = float(data.get('amount', 0))
        
        # Parse date or use today
        date_str = data.get('date')
        if date_str:
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                # Try alternate format
                try:
                    expense_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                except ValueError:
                    expense_date = datetime.now().date()
        else:
            expense_date = datetime.now().date()
        
        # Get other optional fields
        account_id = data.get('account_id')
        notes = data.get('notes', '')
        
        # Use model to predict category
        trainer = get_trainer()
        prediction = trainer.predict_category(description, amount)
        
        # Extract prediction details
        if isinstance(prediction, dict) and prediction.get('success'):
            category = prediction.get('category', 'Miscellaneous')
            confidence = prediction.get('confidence', 0.0)
            explanation = prediction.get('explanation', '')
        else:
            # Fallback to default category if prediction fails
            category = 'Miscellaneous'
            confidence = 0.0
            explanation = 'AI prediction failed'
        
        # Convert any numpy types to standard Python types
        category = convert_numpy_types(category)
        confidence = float(confidence)  # Ensure it's a Python float
        
        try:
            # Create and save the expense
            from models import Expense, db
            
            expense = Expense(
                user_id=current_user.id,
                description=description,
                amount=amount,
                date=expense_date,
                category=category,
                auto_categorized=True,
                categorization_confidence=confidence
            )
            
            if account_id:
                expense.account_id = account_id
                
            db.session.add(expense)
            db.session.commit()
            
            # Build response
            response = {
                'success': True,
                'expense_id': expense.id,
                'category': category,
                'confidence': confidence,
                'explanation': explanation
            }
            
            return safe_jsonify(response)
            
        except Exception as inner_e:
            logger.error(f"Database error in auto_categorize: {str(inner_e)}")
            # Return the category even if saving failed
            return safe_jsonify({
                'success': False,
                'category': category,
                'confidence': confidence,
                'explanation': explanation,
                'error': f"Failed to save expense: {str(inner_e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"Error in auto_categorize: {str(e)}")
        logger.error(traceback.format_exc())
        return safe_jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expense.route('/correction', methods=['POST'])
@login_required
def add_correction():
    """
    Add a user correction to improve the AI model
    
    Request JSON:
    {
        "description": "Expense description text",
        "predicted_category": "Category predicted by AI",
        "correct_category": "Correct category selected by user",
        "amount": (optional) Expense amount,
        "confidence": (optional) AI confidence in prediction,
        "transaction_id": (optional) ID of the expense transaction
    }
    
    Returns:
        JSON with correction result
    """
    try:
        # Get request data
        data = request.get_json()
        logger.info(f"Received correction request: {data}")
        
        # Validate required fields
        required_fields = ['description', 'predicted_category', 'correct_category']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({
                'success': False,
                    'message': f'Missing required field: {field}'
            }), 400
            
        # Get trainer and model version
        trainer = get_trainer()
        model_version = trainer.classifier.model_version
        logger.info(f"Current model version: {model_version}")
        
        # Ensure the AICorrection table exists in the database
        logger.info("Ensuring AICorrection table exists in the database")
        table_exists = AICorrection.ensure_table_exists()
        if not table_exists:
            logger.error("Failed to ensure AICorrection table exists")
            
        # Track if database save was successful
        db_save_success = False
        correction_id = None
        
        try:
            logger.info(f"Attempting to save correction to database with user_id={current_user.id}")
            
            # Use a dedicated session for this transaction
            engine = db.get_engine()
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # First, make sure we're starting with a clean session
            try:
                session.rollback()
            except Exception as tx_error:
                logger.warning(f"Error rolling back session at start: {str(tx_error)}")
            
            try:
                # Create correction object
                correction = AICorrection(
                    user_id=current_user.id,
                    description=data['description'],
                    predicted_category=data['predicted_category'],
                    correct_category=data['correct_category'],
                    amount=data.get('amount'),
                    confidence=data.get('confidence'),
                    transaction_id=data.get('transaction_id'),
                    created_at=datetime.utcnow(),
                    is_applied=False,
                    model_version=model_version
                )
                
                # Add and commit in this dedicated session
                session.add(correction)
                session.commit()
                
                # Get the ID and set success flag
                correction_id = correction.id
                db_save_success = True
                logger.info(f"Successfully saved correction to database with ID: {correction_id}")
                
            except Exception as inner_error:
                logger.error(f"Error in dedicated session: {str(inner_error)}")
                logger.error(traceback.format_exc())
                session.rollback()
                # Don't raise, let it continue to try the trainer save
            finally:
                session.close()
                
            # If dedicated session failed, try the static method as fallback
            if not db_save_success:
                logger.info("Dedicated session failed, trying static method as fallback")
                correction = AICorrection.add_correction(
                    user_id=current_user.id,
                    description=data['description'],
                    predicted_category=data['predicted_category'],
                    correct_category=data['correct_category'],
                    amount=data.get('amount'),
                    confidence=data.get('confidence'),
                    transaction_id=data.get('transaction_id'),
                    model_version=model_version
                )
                
                if correction:
                    db_save_success = True
                    correction_id = correction.id
                    logger.info(f"Successfully saved correction to database with static method, ID: {correction_id}")
                else:
                    logger.warning("Both database save methods failed")
        except Exception as db_error:
            logger.error(f"Database error saving correction: {str(db_error)}")
            logger.error(traceback.format_exc())
        
        # Always add to trainer's in-memory correction store
        # This ensures the model will learn even if DB save fails
        logger.info("Attempting to save correction to trainer's memory")
        trainer_correction = trainer.add_correction(
            user_id=current_user.id,
            description=data['description'],
            predicted_category=data['predicted_category'],
            correct_category=data['correct_category'],
            amount=data.get('amount'),
            confidence=data.get('confidence'),
            transaction_id=data.get('transaction_id')
        )
        
        if trainer_correction:
            logger.info("Successfully saved correction to trainer's memory")
        else:
            logger.warning("Failed to save correction to trainer's memory")
        
        # Return success if either save worked
        if db_save_success or trainer_correction:
            logger.info(f"Correction save result: db_save={db_save_success}, trainer_save={(trainer_correction is not None)}")
            return jsonify({
                'success': True,
                'message': 'Correction saved successfully',
                'correction_id': correction_id,
                'db_saved': db_save_success,
                'trainer_saved': trainer_correction is not None
            })
        else:
            # Both saves failed
            logger.error("Both database and trainer saves failed")
            return jsonify({
                'success': False,
                'message': 'Failed to save correction to both database and trainer'
            }), 400
        
    except Exception as e:
        logger.error(f"Error adding correction: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ai_expense.route('/stats', methods=['GET'])
@login_required
def get_ai_stats():
    """
    Get AI model statistics for the dashboard
    
    Returns:
        JSON with AI model stats
    """
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        # Get trainer
        trainer = get_trainer()
        
        # Get model info
        model_info = trainer.get_model_info()
        
        # Get correction stats
        correction_stats = AICorrection.get_correction_stats()
        
        # Get training history
        training_history = trainer.get_training_history()
        
        # Compile stats
        stats = {
            'model': {
                'version': model_info['version'],
                'accuracy': model_info['accuracy'],
                'last_trained': model_info['last_trained'],
                'categories': len(model_info['categories'])
            },
            'corrections': {
                'total': correction_stats['total'],
                'applied': correction_stats['applied'],
                'unused': correction_stats['unused'],
                'by_category': correction_stats.get('by_category', {}),
                'by_user': correction_stats.get('by_user', {})
            },
            'training': {
                'total_events': len(training_history.get('retraining_events', [])),
                'last_training': training_history.get('last_training'),
                'corrections_applied': training_history.get('total_corrections_applied', 0)
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting AI stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ai_expense.route('/recent-corrections', methods=['GET'])
@login_required
def get_recent_corrections():
    """
    Get recent AI corrections for display
    
    Returns:
        JSON with recent corrections
    """
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        # Get recent corrections
        limit = request.args.get('limit', 50, type=int)
        corrections = AICorrection.get_recent_corrections(limit=limit)
        
        # Format corrections for response
        corrections_list = []
        for correction in corrections:
            corrections_list.append({
                'id': correction.id,
                'user_id': correction.user_id,
                'description': correction.description,
                'predicted_category': correction.predicted_category,
                'correct_category': correction.correct_category,
                'amount': correction.amount,
                'confidence': correction.confidence,
                'created_at': correction.created_at.isoformat(),
                'is_applied': correction.is_applied,
                'applied_at': correction.applied_at.isoformat() if correction.applied_at else None,
                'model_version': correction.model_version,
                'applied_in_version': correction.applied_in_version
            })
        
        return jsonify({
            'success': True,
            'corrections': corrections_list
        })
            
    except Exception as e:
        logger.error(f"Error getting recent corrections: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ai_expense.route('/retrain', methods=['POST'])
@login_required
def retrain_model():
    """
    Retrain the AI model with user corrections
    
    Request JSON:
    {
        "max_corrections": (optional) Maximum number of corrections to use
    }
    
    Returns:
        JSON with retraining results
    """
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        # Get request data
        data = request.get_json() or {}
        max_corrections = data.get('max_corrections')
        logger.info(f"Received retraining request with max_corrections: {max_corrections}")
        
        # Get trainer
        trainer = get_trainer()
        
        # Check for unused corrections before calling retrain
        unused_count = len(AICorrection.get_unused_corrections())
        logger.info(f"Found {unused_count} unused corrections in database")
        
        # Retrain model
        logger.info("Calling retrain_with_corrections")
        results = trainer.retrain_with_corrections(max_corrections=max_corrections)
        logger.info(f"Retrain results: {results}")
        
        if not results.get('success', False):
            error_msg = results.get('message', 'Unknown error retraining model')
            logger.error(f"Retraining failed: {error_msg}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
            
        # Return success
        return jsonify({
            'success': True,
            'message': results['message'],
            'corrections_applied': results['corrections_applied'],
            'model_version': results['model_version'],
            'accuracy': results['accuracy']
        })
        
    except Exception as e:
        logger.error(f"Error retraining model: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ai_expense.route('/model-info', methods=['GET'])
@login_required
def get_model_info():
    """
    Get information about the current AI model
    
    Returns:
        JSON with model information
    """
    try:
        # Get trainer
        trainer = get_trainer()
        
        # Get model info
        model_info = trainer.get_model_info()
        
        # Format info for response
        info = {
            'version': model_info['version'],
            'accuracy': model_info['accuracy'],
            'last_trained': model_info['last_trained'],
            'categories': model_info['categories'],
            'corrections_applied': model_info['corrections_applied'],
            'total_retraining_events': model_info['total_retraining_events']
        }
        
        return jsonify({
            'success': True,
            'model': info
        })
        
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ai_expense.route('/debug/routes', methods=['GET'])
def debug_routes():
    """Return all available routes in the ai_expense blueprint for debugging"""
    routes = []
    
    # Collect all route rules for this blueprint
    from flask import current_app
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint.startswith('ai_expense.'):
            route_data = {
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            }
            routes.append(route_data)
    
    return safe_jsonify({
        'success': True,
        'blueprint_name': ai_expense.name,
        'url_prefix': ai_expense.url_prefix,
        'routes': routes
    })

# Error handlers
@ai_expense.errorhandler(404)
def ai_not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'message': 'API endpoint not found',
        'error': str(error)
    }), 404

@ai_expense.errorhandler(500)
def ai_server_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'message': 'Internal server error',
        'error': str(error)
    }), 500 