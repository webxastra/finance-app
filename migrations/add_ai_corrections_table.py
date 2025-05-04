import sys
import os
from datetime import datetime
import logging

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import app and db
from app import create_app, db
from models.ai_correction import AICorrection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Creates the ai_corrections table for storing AI model corrections.
    This allows the AI to learn from user selections over time.
    """
    app = create_app()
    
    with app.app_context():
        # Check if table already exists
        table_name = 'ai_corrections'
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if table_name in tables:
            logger.info(f"Table '{table_name}' already exists. Migration skipped.")
            return
        
        # Create table
        try:
            logger.info(f"Creating '{table_name}' table...")
            
            # Create table based on model
            db.create_all(tables=[AICorrection.__table__])
            
            logger.info(f"Successfully created '{table_name}' table")
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise
        
        # Commit changes
        db.session.commit()
        logger.info("Migration completed successfully")

if __name__ == "__main__":
    run_migration() 