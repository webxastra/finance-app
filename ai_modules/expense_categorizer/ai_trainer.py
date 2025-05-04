"""
AITrainer

This module handles the training and retraining of the AI model with user corrections.
It manages the correction data flow and model versioning.
"""

import os
import json
import logging
from datetime import datetime
import traceback
from pathlib import Path

from .ai_model import ExpenseClassifier

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AITrainer:
    """
    Manager for AI model training and retraining with user corrections
    """
    
    def __init__(self, base_dir=None):
        """
        Initialize the AI trainer
        
        Args:
            base_dir (str, optional): Base directory for storing models and data
        """
        # Set up directory structure
        if base_dir is None:
            # Default to a directory in the user's home
            base_dir = os.path.join(str(Path.home()), 'finance_app', 'ai')
        
        self.base_dir = base_dir
        self.model_dir = os.path.join(base_dir, 'models')
        self.data_dir = os.path.join(base_dir, 'data')
        self.corrections_path = os.path.join(self.data_dir, 'user_corrections.json')
        self.training_history_path = os.path.join(self.data_dir, 'training_history.json')
        
        # Create required directories
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize classifier
        self.classifier = ExpenseClassifier(model_dir=self.model_dir)
        
        # Load or initialize training history
        self.training_history = self._load_training_history()
        
        # Corrections data
        self.corrections = self._load_corrections()
    
    def _load_training_history(self):
        """Load training history from file"""
        if os.path.exists(self.training_history_path):
            try:
                with open(self.training_history_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading training history: {str(e)}")
        
        # Default empty history
        return {
            'versions': [],
            'last_training': None,
            'total_corrections_applied': 0,
            'retraining_events': []
        }
    
    def _save_training_history(self):
        """Save training history to file"""
        try:
            with open(self.training_history_path, 'w') as f:
                json.dump(self.training_history, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving training history: {str(e)}")
            return False
    
    def _load_corrections(self):
        """Load user corrections from file"""
        if os.path.exists(self.corrections_path):
            try:
                with open(self.corrections_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading corrections: {str(e)}")
        
        # Default empty corrections
        return {
            'unused': [],  # Corrections not yet used for training
            'applied': []  # Corrections already applied to the model
        }
    
    def _save_corrections(self):
        """Save user corrections to file"""
        try:
            with open(self.corrections_path, 'w') as f:
                json.dump(self.corrections, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving corrections: {str(e)}")
            return False
    
    def add_correction(self, user_id, description, predicted_category, correct_category, 
                      amount=None, confidence=None, transaction_id=None):
        """
        Add a new user correction
        
        Args:
            user_id (int): ID of the user making the correction
            description (str): Transaction description text
            predicted_category (str): Category predicted by AI
            correct_category (str): Category selected by user
            amount (float, optional): Transaction amount
            confidence (float, optional): AI's confidence in the prediction
            transaction_id (int, optional): Link to expense ID
            
        Returns:
            dict: Added correction or None if failed
        """
        try:
            # If transaction_id is provided, check for duplicate
            if transaction_id:
                for existing in self.corrections['unused']:
                    if existing.get('transaction_id') == transaction_id:
                        logger.info(f"Skipping duplicate correction for transaction_id {transaction_id}")
                        return existing
            
            # Create correction object with next available ID
            next_id = 1
            
            # Find the highest ID currently in use
            all_ids = [c.get('id', 0) for c in self.corrections['unused'] + self.corrections['applied']]
            if all_ids:
                next_id = max(all_ids) + 1
                
            # Create the correction
            correction = {
                'id': next_id,
                'user_id': user_id,
                'description': description,
                'predicted_category': predicted_category,
                'correct_category': correct_category,
                'created_at': datetime.now().isoformat(),
                'is_applied': False
            }
            
            # Add optional fields
            if amount is not None:
                correction['amount'] = float(amount)
            
            if confidence is not None:
                correction['confidence'] = float(confidence)
                
            if transaction_id is not None:
                correction['transaction_id'] = transaction_id
            
            # Add to unused corrections
            self.corrections['unused'].append(correction)
            
            # Save corrections
            self._save_corrections()
            
            logger.info(f"Added correction: {description} - {predicted_category} -> {correct_category}")
            return correction
            
        except Exception as e:
            logger.error(f"Failed to add correction: {str(e)}")
            return None
    
    def get_unused_corrections(self, limit=None):
        """
        Get corrections that haven't been applied yet
        
        Args:
            limit (int, optional): Maximum number to return
            
        Returns:
            list: Unused corrections
        """
        # First check for corrections in the database
        try:
            # Import here to avoid circular imports
            from models.ai_correction import AICorrection
            
            # Log the check
            logger.info("Checking for unused corrections in database")
            
            # Get unused corrections from database
            db_corrections = AICorrection.get_unused_corrections(limit=limit)
            
            if db_corrections:
                logger.info(f"Found {len(db_corrections)} unused corrections in database")
                
                # Convert database corrections to the format used by this class
                formatted_corrections = []
                for correction in db_corrections:
                    formatted = {
                        'id': correction.id,
                        'user_id': correction.user_id,
                        'description': correction.description,
                        'predicted_category': correction.predicted_category,
                        'correct_category': correction.correct_category,
                        'created_at': correction.created_at.isoformat() if hasattr(correction.created_at, 'isoformat') else str(correction.created_at),
                        'is_applied': False
                    }
                    
                    # Add optional fields if present
                    if hasattr(correction, 'amount') and correction.amount is not None:
                        formatted['amount'] = float(correction.amount)
                    
                    if hasattr(correction, 'confidence') and correction.confidence is not None:
                        formatted['confidence'] = float(correction.confidence)
                    
                    if hasattr(correction, 'transaction_id') and correction.transaction_id is not None:
                        formatted['transaction_id'] = correction.transaction_id
                    
                    formatted_corrections.append(formatted)
                
                return formatted_corrections
        except Exception as e:
            logger.error(f"Error retrieving corrections from database: {str(e)}")
            logger.error(traceback.format_exc())
            logger.warning("Falling back to in-memory correction storage")
        
        # Fall back to memory-based corrections if database retrieval fails
        unused = self.corrections['unused']
        if limit and len(unused) > limit:
            return unused[:limit]
            
        logger.info(f"Using {len(unused)} corrections from in-memory storage")
        return unused
    
    def get_correction_stats(self):
        """
        Get statistics about corrections
        
        Returns:
            dict: Correction statistics
        """
        # Count corrections by category
        category_stats = {}
        
        # Process unused corrections
        for correction in self.corrections['unused']:
            category = correction['correct_category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'applied': 0, 'unused': 0}
            
            category_stats[category]['total'] += 1
            category_stats[category]['unused'] += 1
        
        # Process applied corrections
        for correction in self.corrections['applied']:
            category = correction['correct_category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'applied': 0, 'unused': 0}
            
            category_stats[category]['total'] += 1
            category_stats[category]['applied'] += 1
        
        # Overall stats
        total = len(self.corrections['unused']) + len(self.corrections['applied'])
        applied = len(self.corrections['applied'])
        unused = len(self.corrections['unused'])
        
        return {
            'total': total,
            'applied': applied,
            'unused': unused,
            'categories': category_stats
        }
    
    def train_initial_model(self, training_data=None):
        """
        Train the initial model with default or provided data
        
        Args:
            training_data (dict, optional): Dictionary with 'descriptions' and 'categories' lists
            
        Returns:
            dict: Training results
        """
        try:
            # If no data provided, use default categories with synthetic examples
            if not training_data:
                # Create basic examples for each category
                descriptions = []
                categories = []
                
                for category in self.classifier.categories:
                    # Create category-specific keywords
                    keywords = self._get_category_keywords(category)
                    
                    # Create examples using these keywords
                    for i in range(5):  # 5 examples per category
                        if i < len(keywords):
                            # Use different combinations of words
                            if i == 0:
                                desc = f"{keywords[0]}"
                            elif i == 1 and len(keywords) > 1:
                                desc = f"{keywords[0]} {keywords[1]}"
                            elif i == 2 and len(keywords) > 2:
                                desc = f"{keywords[0]} {keywords[1]} {keywords[2]}"
                            elif i == 3 and len(keywords) > 1:
                                desc = f"{keywords[1]}"
                            elif i == 4 and len(keywords) > 2:
                                desc = f"{keywords[2]}"
                            else:
                                desc = f"{keywords[0]}"
                                
                            descriptions.append(desc)
                            categories.append(category)
            else:
                # Use provided data
                descriptions = training_data['descriptions']
                categories = training_data['categories']
            
            # Train the model
            results = self.classifier.train(descriptions, categories)
            
            # Update training history
            self._update_training_history(results, is_initial=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error training initial model: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _get_category_keywords(self, category):
        """Get sample keywords for a category"""
        category_keywords = {
            'Food & Dining': ['restaurant', 'cafe', 'grocery', 'coffee', 'meal', 'food'],
            'Transportation': ['gas', 'fuel', 'taxi', 'uber', 'car', 'bus', 'train'],
            'Housing': ['rent', 'mortgage', 'apartment', 'house', 'property'],
            'Utilities': ['electricity', 'water', 'gas', 'internet', 'phone', 'bill'],
            'Healthcare': ['doctor', 'hospital', 'medication', 'pharmacy', 'medical'],
            'Entertainment': ['movie', 'theater', 'concert', 'netflix', 'subscription'],
            'Shopping': ['clothes', 'shoes', 'retail', 'mall', 'amazon', 'purchase'],
            'Personal Care': ['haircut', 'salon', 'spa', 'cosmetics', 'gym'],
            'Education': ['tuition', 'books', 'course', 'school', 'university'],
            'Travel': ['hotel', 'flight', 'vacation', 'airbnb', 'booking'],
            'Gifts & Donations': ['gift', 'donation', 'charity', 'present'],
            'Insurance': ['insurance', 'premium', 'coverage', 'policy'],
            'Taxes': ['tax', 'irs', 'government', 'filing'],
            'Business Services': ['consultant', 'service', 'contractor', 'professional'],
            'Investments': ['investment', 'stock', 'mutual fund', 'broker', 'retirement'],
            'Miscellaneous': ['other', 'misc', 'unknown', 'general']
        }
        
        return category_keywords.get(category, ['general', 'purchase'])
    
    def retrain_with_corrections(self, max_corrections=None):
        """
        Retrain the model with user corrections
        
        Args:
            max_corrections (int, optional): Maximum number of corrections to use
            
        Returns:
            dict: Retraining results
        """
        try:
            # Get unused corrections
            unused_corrections = self.get_unused_corrections(limit=max_corrections)
            
            if not unused_corrections:
                logger.info("No unused corrections available for retraining")
                return {
                    'success': False,
                    'message': 'No unused corrections available'
                }
            
            # Ensure model is initialized
            if not self.classifier.is_trained:
                logger.info("Model not initialized, training initial model first")
                self.train_initial_model()
                
                if not self.classifier.is_trained:
                    logger.error("Failed to initialize model")
                    return {
                        'success': False,
                        'message': 'Failed to initialize model'
                    }
            
            # Prepare correction data for training
            training_data = []
            correction_ids = []
            
            for correction in unused_corrections:
                training_data.append({
                    'description': correction['description'],
                    'category': correction['correct_category']
                })
                correction_ids.append(correction['id'])
            
            # Retrain the model
            results = self.classifier.add_training_data(training_data)
            
            if not results:
                logger.error("Failed to retrain model")
                return {
                    'success': False,
                    'message': 'Failed to retrain model'
                }
            
            # Mark corrections as applied
            self._mark_corrections_as_applied(correction_ids)
            
            # Update training history
            self._update_training_history(results, 
                                          corrections_applied=len(training_data),
                                          correction_ids=correction_ids)
            
            return {
                'success': True,
                'message': 'Model retrained successfully',
                'corrections_applied': len(training_data),
                'model_version': self.classifier.model_version - 1,
                'accuracy': results.get('accuracy', None)
            }
            
        except Exception as e:
            logger.error(f"Error retraining model: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _mark_corrections_as_applied(self, correction_ids):
        """
        Mark corrections as applied
        
        Args:
            correction_ids (list): IDs of corrections to mark
        """
        # First mark corrections as applied in the database
        try:
            # Import here to avoid circular imports
            from models.ai_correction import AICorrection
            
            # Log the update
            logger.info(f"Marking {len(correction_ids)} corrections as applied in database")
            
            # Mark as applied in database
            updated_count = AICorrection.mark_as_applied(correction_ids, model_version=self.classifier.model_version - 1)
            logger.info(f"Updated {updated_count} corrections in database")
            
        except Exception as e:
            logger.error(f"Error marking corrections as applied in database: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Also update our in-memory correction store
        # Move corrections from unused to applied
        newly_applied = []
        remaining_unused = []
        
        for correction in self.corrections['unused']:
            if correction['id'] in correction_ids:
                # Mark as applied
                correction['is_applied'] = True
                correction['applied_at'] = datetime.now().isoformat()
                correction['applied_in_version'] = self.classifier.model_version - 1
                newly_applied.append(correction)
            else:
                remaining_unused.append(correction)
        
        # Update corrections
        self.corrections['unused'] = remaining_unused
        self.corrections['applied'].extend(newly_applied)
        
        # Save corrections
        self._save_corrections()
        
        logger.info(f"Marked {len(newly_applied)} corrections as applied in memory storage")
        
        # Reload corrections to ensure we have the latest state
        self._load_corrections()
    
    def _update_training_history(self, results, is_initial=False, 
                                corrections_applied=0, correction_ids=None):
        """Update training history with new training event"""
        # Get current version (after training, version is incremented)
        current_version = self.classifier.model_version - 1
        
        # Add version to versions list if not already there
        if current_version not in self.training_history['versions']:
            self.training_history['versions'].append(current_version)
        
        # Update last training timestamp
        self.training_history['last_training'] = datetime.now().isoformat()
        
        # Update total corrections applied
        self.training_history['total_corrections_applied'] += corrections_applied
        
        # Add retraining event
        event = {
            'timestamp': datetime.now().isoformat(),
            'version': current_version,
            'is_initial': is_initial,
            'metrics': {
                'accuracy': results.get('accuracy', None),
                'f1_score': results.get('f1_score', None),
                'samples': results.get('train_samples', 0) + results.get('test_samples', 0)
            },
            'corrections_applied': corrections_applied
        }
        
        if correction_ids:
            event['correction_ids'] = correction_ids
        
        self.training_history['retraining_events'].append(event)
        
        # Save training history
        self._save_training_history()
    
    def predict_category(self, description, amount=None):
        """
        Predict category for an expense description
        
        Args:
            description (str): Expense description
            amount (float, optional): Expense amount
            
        Returns:
            dict: Prediction results
        """
        # Ensure model is trained
        if not self.classifier.is_trained:
            # Try to load a saved model
            loaded = self.classifier.load()
            
            if not loaded:
                # Train initial model
                self.train_initial_model()
                
                if not self.classifier.is_trained:
                    logger.error("Failed to initialize model")
                    return {
                        'success': False,
                        'message': 'No trained model available'
                    }
        
        # Check for user corrections (global override)
        try:
            desc_norm = description.strip().lower()
            amt_norm = float(amount) if amount is not None else None
            all_corrections = self.corrections.get('unused', []) + self.corrections.get('applied', [])
            match = None
            for corr in all_corrections:
                corr_desc = str(corr.get('description', '')).strip().lower()
                corr_amt = corr.get('amount', None)
                # If amount is present in both, require match; else match by description only
                if corr_desc == desc_norm:
                    if amt_norm is not None and corr_amt is not None:
                        try:
                            if float(corr_amt) == amt_norm:
                                match = corr
                                break
                        except Exception:
                            continue
                    elif amt_norm is None or corr_amt is None:
                        match = corr
                        break
            if match:
                # Correction found, override
                return {
                    'category': match['correct_category'],
                    'confidence': 1.0,
                    'alternatives': [],
                    'explanation': f"This category was set by your previous correction and will always override the AI prediction.",
                    'model_version': self.classifier.model_version,
                    'success': True,
                    'source': 'user_correction'
                }
            # No correction, proceed with model prediction
            prediction = self.classifier.predict(description)
            prediction['model_version'] = self.classifier.model_version
            prediction['success'] = True
            return prediction
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_training_history(self):
        """Get model training history"""
        return self.training_history
    
    def get_model_info(self):
        """Get information about the current model"""
        return {
            'version': self.classifier.model_version,
            'is_trained': self.classifier.is_trained,
            'last_trained': self.classifier.last_trained.isoformat() if self.classifier.last_trained else None,
            'accuracy': self.classifier.accuracy,
            'categories': self.classifier.categories,
            'corrections_applied': self.training_history.get('total_corrections_applied', 0),
            'total_retraining_events': len(self.training_history.get('retraining_events', []))
        }
    
    def train_with_default_data(self):
        """
        Train the model with default data from training_data.py
        
        Returns:
            float: Accuracy of the trained model
        """
        try:
            # Import the default training data
            from .training_data import MAIN_CATEGORY_TRAINING_DATA
            
            # Get the data
            descriptions = MAIN_CATEGORY_TRAINING_DATA['descriptions']
            categories = MAIN_CATEGORY_TRAINING_DATA['categories']
            
            # Ensure we have enough data for each category
            # Minimum test size required is 16 (number of categories)
            test_size = max(0.2, 16/len(descriptions))
            
            # Train the model with a test_size that ensures at least one example of each category is in the test set
            results = self.classifier.train(descriptions, categories, test_size=test_size)
            
            # Update training history
            self._update_training_history(results, is_initial=True)
            
            return results.get('accuracy', 0.0)
            
        except Exception as e:
            logger.error(f"Error training with default data: {str(e)}")
            logger.error(traceback.format_exc())
            return 0.0 