"""
API Routes Module
Provides base API routes for the application
This module defines shared API routes and utilities
"""

from flask import Blueprint, jsonify, request, current_app, g
from flask_login import login_required, current_user
from models import db, Expense, AICorrection, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from ai_modules.expense_categorizer.categorizer import ExpenseCategorizer
from ai_modules.expense_categorizer.service import convert_numpy_types
import logging
import os
from utils.json_utils import safe_jsonify
from sqlalchemy import inspect

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Configure API base URL for external services
API_BASE_URL = os.environ.get('EXPRESS_API_URL', 'http://localhost:8000/api')


@api.route('/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'API is running'
    }), 200


@api.route('/user/current', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user information"""
    if not current_user.is_authenticated:
        return jsonify({
            'status': 'error',
            'message': 'Not authenticated'
        }), 401
    
    return jsonify({
        'status': 'success',
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'salary': float(current_user.salary)
        }
    }), 200


@api.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_by_id(user_id):
    """Get user information by ID"""
    # For security, only allow users to access their own information
    if user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized to access this user information'
        }), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'salary': float(user.salary)
        }
    }), 200


@api.route('/ai/expenses/correction', methods=['POST'])
@login_required
def add_ai_correction():
    """Endpoint to save user corrections to AI model predictions."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'description' not in data or 'correct_category' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required fields. Please provide description and correct_category.'
            }), 400
            
        # Get data from request
        description = data.get('description')
        correct_category = data.get('correct_category')
        amount = data.get('amount')
        predicted_category = data.get('predicted_category')  # Optional
        confidence = data.get('confidence')  # Optional
        transaction_id = data.get('transaction_id')  # Optional
        
        # Add correction to database
        correction = AICorrection.add_correction(
            user_id=current_user.id,
            description=description,
            correct_category=correct_category,
            predicted_category=predicted_category,
            amount=amount,
            confidence=confidence,
            transaction_id=transaction_id
        )
        
        if correction:
            return jsonify({
                'success': True,
                'message': 'Correction saved successfully',
                'correction_id': correction.id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Not saved. Predicted category matches correct category or other error occurred.'
            }), 400
            
    except Exception as e:
        logger.error(f"Error adding AI correction: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to add correction: {str(e)}'
        }), 500


@api.route('/ai/training/correction-stats', methods=['GET'])
@login_required
def get_correction_stats():
    """Get statistics about AI corrections for admin dashboard."""
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        # Ensure the table exists first
        if not AICorrection.ensure_table_exists():
            # Return empty stats if we couldn't ensure table exists
            return safe_jsonify({
                'success': True,
                'total_corrections': 0,
                'applied_corrections': 0,
                'unused_corrections': 0,
                'category_counts': {}
            })
            
        # Get the stats from the AICorrection model
        stats = AICorrection.get_correction_stats()
        
        return safe_jsonify({
            'success': True,
            'total_corrections': stats['total'],
            'applied_corrections': stats['applied'],
            'unused_corrections': stats['unused'],
            'category_counts': stats['categories']
        })
        
    except Exception as e:
        logger.error(f"Error getting correction stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get correction stats: {str(e)}'
        }), 500


@api.route('/ai/training/recent-corrections', methods=['GET'])
@login_required
def get_recent_corrections():
    """Get recent AI corrections for admin dashboard."""
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        # Ensure the table exists first
        if not AICorrection.ensure_table_exists():
            # Return empty result if we couldn't ensure table exists
            return safe_jsonify({
                'success': True,
                'corrections': []
            })
            
        # Get the 50 most recent corrections
        corrections = AICorrection.query.order_by(AICorrection.created_at.desc()).limit(50).all()
        
        corrections_list = []
        for correction in corrections:
            corrections_list.append({
                'id': correction.id,
                'user_id': correction.user_id,
                'description': correction.description,
                'amount': correction.amount,
                'predicted_category': correction.predicted_category,
                'correct_category': correction.correct_category,
                'confidence': correction.confidence,
                'transaction_id': correction.transaction_id,
                'created_at': correction.created_at.isoformat(),
                'is_applied': correction.is_applied
            })
        
        return safe_jsonify({
            'success': True,
            'corrections': corrections_list
        })
        
    except Exception as e:
        logger.error(f"Error getting recent corrections: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get recent corrections: {str(e)}'
        }), 500


@api.route('/ai/training/retrain-with-corrections', methods=['POST'])
@login_required
def retrain_with_corrections():
    """Retrain the AI model with user corrections."""
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        # Ensure the table exists first
        if not AICorrection.ensure_table_exists():
            return jsonify({
                'success': False,
                'message': 'No corrections available - the AI corrections table does not exist yet or cannot be created'
            }), 400
            
        # Get unused corrections
        unused_corrections = AICorrection.get_unused_corrections()
        
        if not unused_corrections:
            return jsonify({
                'success': False,
                'message': 'No unused corrections available for training'
            }), 400
            
        # Get the categorizer instance
        use_detailed = request.json.get('use_detailed', False) if request.json else False
        
        # Make sure the app has categorizers initialized
        if not hasattr(current_app, 'ai_categorizer') or current_app.ai_categorizer is None:
            from ai_modules.expense_categorizer.categorizer import ExpenseCategorizer
            current_app.ai_categorizer = ExpenseCategorizer(use_detailed_categories=False)
            current_app.ai_categorizer.train_with_default_data()
        
        if use_detailed:
            if not hasattr(current_app, 'ai_detailed_categorizer') or current_app.ai_detailed_categorizer is None:
                from ai_modules.expense_categorizer.categorizer import ExpenseCategorizer
                current_app.ai_detailed_categorizer = ExpenseCategorizer(use_detailed_categories=True)
                current_app.ai_detailed_categorizer.train_with_default_data(use_detailed=True)
            categorizer = current_app.ai_detailed_categorizer
        else:
            categorizer = current_app.ai_categorizer
        
        # Prepare correction data for training
        training_data = []
        for correction in unused_corrections:
            training_data.append({
                'description': correction.description, 
                'category': correction.correct_category
            })
            
        # Retrain model with corrections
        accuracy = categorizer.add_training_data(training_data)
        
        # Mark corrections as applied
        correction_ids = [c.id for c in unused_corrections]
        AICorrection.mark_as_applied(correction_ids)
        
        return safe_jsonify({
            'success': True,
            'message': 'Model retrained successfully with user corrections',
            'corrections_applied': len(unused_corrections),
            'accuracy': accuracy
        })
        
    except Exception as e:
        logger.error(f"Error retraining model with corrections: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to retrain model: {str(e)}'
        }), 500


from flask import send_file
import io
import pandas as pd

@api.route('/ai/training/reset-model', methods=['POST'])
@login_required
def reset_model():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    try:
        # Reset model (re-initialize and retrain with default data)
        from ai_modules.expense_categorizer.categorizer import ExpenseCategorizer
        current_app.ai_categorizer = ExpenseCategorizer(use_detailed_categories=False)
        acc = current_app.ai_categorizer.train_with_default_data()
        # Optionally clear corrections
        AICorrection.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Model reset to default and corrections cleared', 'accuracy': acc})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting model: {e}")
        return jsonify({'success': False, 'message': f'Failed to reset model: {str(e)}'}), 500

@api.route('/ai/training/download-model', methods=['GET'])
@login_required
def download_model():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    try:
        model_path = current_app.ai_categorizer.model_path if hasattr(current_app.ai_categorizer, 'model_path') else 'model.pkl'
        return send_file(model_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return jsonify({'success': False, 'message': f'Failed to download model: {str(e)}'}), 500

@api.route('/ai/training/export-corrections', methods=['GET'])
@login_required
def export_corrections():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    try:
        format = request.args.get('format', 'json')
        corrections = AICorrection.query.order_by(AICorrection.created_at.desc()).all()
        data = [
            {
                'id': c.id,
                'user_id': c.user_id,
                'description': c.description,
                'amount': c.amount,
                'predicted_category': c.predicted_category,
                'correct_category': c.correct_category,
                'confidence': c.confidence,
                'transaction_id': c.transaction_id,
                'created_at': c.created_at,
                'is_applied': c.is_applied
            } for c in corrections
        ]
        if format == 'csv':
            df = pd.DataFrame(data)
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            buf.seek(0)
            return send_file(io.BytesIO(buf.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='corrections.csv')
        else:
            return jsonify({'success': True, 'corrections': data})
    except Exception as e:
        logger.error(f"Error exporting corrections: {e}")
        return jsonify({'success': False, 'message': f'Failed to export corrections: {str(e)}'}), 500

@api.route('/ai/training/delete-correction/<int:correction_id>', methods=['DELETE'])
@login_required
def delete_correction(correction_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    try:
        correction = AICorrection.query.get(correction_id)
        if not correction:
            return jsonify({'success': False, 'message': 'Correction not found'}), 404
        db.session.delete(correction)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Correction deleted'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting correction: {e}")
        return jsonify({'success': False, 'message': f'Failed to delete correction: {str(e)}'}), 500

# Error handling for API routes
@api.errorhandler(404)
def api_not_found(error):
    """Handle 404 errors for API routes"""
    return jsonify({
        'status': 'error',
        'message': 'API endpoint not found',
        'error': str(error)
    }), 404


@api.errorhandler(500)
def api_server_error(error):
    """Handle 500 errors for API routes"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': str(error)
    }), 500 