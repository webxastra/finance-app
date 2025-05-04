"""
Add explanation field to expenses table

This migration adds the auto_categorization_explanation column to the expenses table.
"""

import sys
import os

# Add the parent directory to the path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from db import db
from sqlalchemy import Column, String, text
import traceback

def upgrade():
    """Add auto_categorization_explanation column to expenses table"""
    try:
        with app.app_context():
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('expenses')]
            
            if 'auto_categorization_explanation' not in columns:
                # Add the column
                db.session.execute(text('ALTER TABLE expenses ADD COLUMN auto_categorization_explanation VARCHAR(255)'))
                db.session.commit()
                print("Added auto_categorization_explanation column to expenses table")
            else:
                print("Column auto_categorization_explanation already exists")
                
            return True
    except Exception as e:
        print(f"Error adding column: {str(e)}")
        traceback.print_exc()
        return False

def downgrade():
    """Remove auto_categorization_explanation column from expenses table"""
    try:
        with app.app_context():
            # Check if the column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('expenses')]
            
            if 'auto_categorization_explanation' in columns:
                # Remove the column
                db.session.execute(text('ALTER TABLE expenses DROP COLUMN auto_categorization_explanation'))
                db.session.commit()
                print("Removed auto_categorization_explanation column from expenses table")
            else:
                print("Column auto_categorization_explanation does not exist")
                
            return True
    except Exception as e:
        print(f"Error removing column: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Execute upgrade when the script is run directly
    upgrade() 