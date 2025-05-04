"""
AI Correction Model

This module defines the database model for user corrections to AI predictions.
These corrections are used to retrain and improve the AI model over time.
"""

import logging
import datetime as dt
import traceback
from db import db
from sqlalchemy import text
from models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AICorrection(db.Model):
    """
    Model to store AI category corrections from users.
    Used to improve the AI model over time through retraining.
    """
    __tablename__ = 'ai_corrections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    predicted_category = db.Column(db.String(50), nullable=False)
    correct_category = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=True)  # AI's confidence in the prediction
    transaction_id = db.Column(db.Integer, nullable=True)  # Optional link to expense ID
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    is_applied = db.Column(db.Boolean, default=False)  # Has this correction been applied in retraining
    applied_at = db.Column(db.DateTime, nullable=True)  # When this correction was used for retraining
    model_version = db.Column(db.Integer, nullable=True)  # Model version when correction was made
    applied_in_version = db.Column(db.Integer, nullable=True)  # Model version that included this correction
    
    # Relationship with user
    user = db.relationship('User', backref=db.backref('ai_corrections', lazy=True))
    
    def __repr__(self):
        return f"<AICorrection {self.id}: {self.predicted_category} -> {self.correct_category}>"
    
    @classmethod
    def ensure_table_exists(cls):
        """Ensure the ai_corrections table exists in the database"""
        from sqlalchemy import inspect
        
        try:
            inspector = inspect(db.engine)
            if cls.__tablename__ not in inspector.get_table_names():
                logger.info(f"Creating {cls.__tablename__} table")
                cls.__table__.create(db.engine)
                logger.info(f"Successfully created {cls.__tablename__} table")
                return True
            
            # Table exists, check if it has the new columns
            columns = inspector.get_columns(cls.__tablename__)
            column_names = [col['name'] for col in columns]
            
            # Check for new columns added in this implementation
            new_columns = ['applied_at', 'model_version', 'applied_in_version']
            missing_columns = [col for col in new_columns if col not in column_names]
            
            # If missing some new columns, add them
            if missing_columns:
                logger.info(f"Adding missing columns to {cls.__tablename__}: {missing_columns}")
                
                # Add missing columns using SQL directly
                with db.engine.connect() as conn:
                    for column in missing_columns:
                        if column == 'applied_at':
                            conn.execute(text(f"ALTER TABLE {cls.__tablename__} ADD COLUMN {column} DATETIME"))
                        elif column in ['model_version', 'applied_in_version']:
                            conn.execute(text(f"ALTER TABLE {cls.__tablename__} ADD COLUMN {column} INTEGER"))
                
                logger.info(f"Successfully added missing columns")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring {cls.__tablename__} table exists: {str(e)}")
            try:
                # Create table directly if needed
                db.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {cls.__tablename__} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    description VARCHAR(200) NOT NULL,
                    amount FLOAT,
                    predicted_category VARCHAR(50) NOT NULL,
                    correct_category VARCHAR(50) NOT NULL,
                    confidence FLOAT,
                    transaction_id INTEGER,
                    created_at DATETIME,
                    is_applied BOOLEAN DEFAULT 0,
                    applied_at DATETIME,
                    model_version INTEGER,
                    applied_in_version INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                """))
                db.session.commit()
                logger.info(f"Created {cls.__tablename__} table using direct SQL")
                return True
            except Exception as e2:
                logger.error(f"Failed to create {cls.__tablename__} table with direct SQL: {str(e2)}")
                return False
    
    @staticmethod
    def add_correction(user_id, description, predicted_category, correct_category, 
                     amount=None, confidence=None, transaction_id=None, model_version=None):
        """
        Add a new correction to the database
        
        Args:
            user_id: ID of the user making the correction
            description: Transaction description text
            predicted_category: Category predicted by AI
            correct_category: Category selected by user
            amount: Optional transaction amount
            confidence: AI's confidence in the prediction
            transaction_id: Optional link to expense ID
            model_version: Version of the model that made the prediction
            
        Returns:
            The created AICorrection object or None if failed
        """
        # First ensure the table exists
        if not AICorrection.ensure_table_exists():
            logger.error("Cannot add correction: table does not exist")
            return None
            
        # REMOVED validation check to accept all corrections regardless of predicted category
        # This allows users to submit corrections even when the system thinks they're unnecessary
            
        try:
            # Double-check for any uncommitted transactions and rollback if needed
            try:
                db.session.rollback()
                logger.info("Session rolled back before creating new correction")
            except Exception as tx_error:
                logger.warning(f"Error rolling back session: {str(tx_error)}")

            # Create the correction object
            correction = AICorrection(
                user_id=user_id,
                description=description,
                predicted_category=predicted_category,
                correct_category=correct_category,
                amount=amount,
                confidence=confidence,
                transaction_id=transaction_id,
                created_at=dt.datetime.utcnow(),
                is_applied=False,
                model_version=model_version
            )
            
            # Log the object
            logger.info(f"Created correction object: {correction}")
            
            # Add to session and commit - with a retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    db.session.add(correction)
                    db.session.commit()
                    logger.info(f"Successfully added correction to database (attempt {attempt+1})")
                    return correction
                except Exception as commit_error:
                    logger.error(f"Error committing correction (attempt {attempt+1}): {str(commit_error)}")
                    db.session.rollback()
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying database save (attempt {attempt+2})...")
                    else:
                        logger.error(f"Failed to save correction after {max_retries} attempts")
                        return None
            
        except Exception as e:
            logger.error(f"Error adding correction: {str(e)}")
            logger.error(traceback.format_exc())
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    @staticmethod
    def get_unused_corrections(limit=None):
        """
        Get corrections that haven't been applied to the model yet
        
        Args:
            limit: Optional maximum number of corrections to return
            
        Returns:
            List of AICorrection objects
        """
        # First ensure the table exists
        if not AICorrection.ensure_table_exists():
            logger.warning("Cannot get unused corrections: table does not exist")
            return []
            
        query = AICorrection.query.filter_by(is_applied=False).order_by(AICorrection.created_at)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def mark_as_applied(correction_ids, model_version=None):
        """
        Mark corrections as applied after retraining
        
        Args:
            correction_ids: List of correction IDs that were applied
            model_version: Version of the model that includes these corrections
            
        Returns:
            Number of corrections updated
        """
        # First ensure the table exists
        if not AICorrection.ensure_table_exists():
            logger.warning("Cannot mark corrections as applied: table does not exist")
            return 0
            
        if not correction_ids:
            logger.warning("No correction IDs provided to mark as applied")
            return 0
        
        try:
            # Log what we're about to do
            logger.info(f"Marking corrections as applied: IDs={correction_ids}, model_version={model_version}")
            
            # Start a transaction
            db.session.begin()
            
            # Update corrections with retry mechanism
            max_retries = 3
            updated_count = 0
            
            for attempt in range(max_retries):
                try:
                    now = dt.datetime.utcnow()
                    
                    # Get the corrections to update
                    corrections = AICorrection.query.filter(AICorrection.id.in_(correction_ids)).all()
                    
                    if not corrections:
                        logger.warning(f"No corrections found with IDs: {correction_ids}")
                        db.session.rollback()
                        return 0
                    
                    # Update each correction
                    for correction in corrections:
                        correction.is_applied = True
                        correction.applied_at = now
                        correction.applied_in_version = model_version
                        db.session.add(correction)
                    
                    # Commit the transaction
                    db.session.commit()
                    updated_count = len(corrections)
                    logger.info(f"Successfully marked {updated_count} corrections as applied (attempt {attempt+1})")
                    return updated_count
                    
                except Exception as update_error:
                    logger.error(f"Error updating corrections (attempt {attempt+1}): {str(update_error)}")
                    logger.error(traceback.format_exc())
                    db.session.rollback()
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying update (attempt {attempt+2})...")
                    else:
                        logger.error(f"Failed to mark corrections as applied after {max_retries} attempts")
                        return 0
            
            return updated_count
                
        except Exception as e:
            logger.error(f"Error marking corrections as applied: {str(e)}")
            logger.error(traceback.format_exc())
            try:
                db.session.rollback()
            except:
                pass
            return 0
    
    @staticmethod
    def get_correction_stats():
        """
        Get statistics about corrections
        
        Returns:
            Dictionary with correction statistics
        """
        # First ensure the table exists
        if not AICorrection.ensure_table_exists():
            logger.warning("Cannot get correction stats: table does not exist")
            return {
                'total': 0,
                'applied': 0,
                'unused': 0,
                'by_category': {},
                'by_user': {}
            }
            
        try:
            # Get counts using SQL queries for efficiency
            total = db.session.query(AICorrection).count()
            applied = db.session.query(AICorrection).filter_by(is_applied=True).count()
            unused = db.session.query(AICorrection).filter_by(is_applied=False).count()
            
            # Get corrections by category
            category_counts = db.session.query(
                AICorrection.correct_category, 
                db.func.count(AICorrection.id)
            ).group_by(AICorrection.correct_category).all()
            
            by_category = {cat: count for cat, count in category_counts}
            
            # Get corrections by user
            user_counts = db.session.query(
                AICorrection.user_id, 
                db.func.count(AICorrection.id)
            ).group_by(AICorrection.user_id).all()
            
            by_user = {str(user_id): count for user_id, count in user_counts}
            
            return {
                'total': total,
                'applied': applied,
                'unused': unused,
                'by_category': by_category,
                'by_user': by_user
            }
            
        except Exception as e:
            logger.error(f"Error getting correction stats: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'total': 0,
                'applied': 0,
                'unused': 0,
                'by_category': {},
                'by_user': {}
            }
    
    @staticmethod
    def get_recent_corrections(limit=50, offset=0):
        """
        Get recent corrections
        
        Args:
            limit: Maximum number of corrections to return
            offset: Number of corrections to skip (for pagination)
            
        Returns:
            List of AICorrection objects
        """
        # First ensure the table exists
        if not AICorrection.ensure_table_exists():
            logger.warning("Cannot get recent corrections: table does not exist")
            return []
            
        try:
            # Get corrections with pagination
            corrections = AICorrection.query.order_by(
                AICorrection.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return corrections
            
        except Exception as e:
            logger.error(f"Error getting recent corrections: {str(e)}")
            logger.error(traceback.format_exc())
            return [] 