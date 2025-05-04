"""
Database Utilities for the Finance App

This module provides utility functions for database operations,
particularly those related to schema validation and ensuring
tables exist before querying.
"""

from sqlalchemy import inspect
from models import db
import logging

logger = logging.getLogger(__name__)

def table_exists(table_name):
    """
    Check if a table exists in the database
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        bool: True if the table exists, False otherwise
    """
    try:
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()
    except Exception as e:
        logger.error(f"Error checking if table {table_name} exists: {str(e)}")
        return False

def create_table_if_not_exists(model_class):
    """
    Create a table if it doesn't exist yet
    
    Args:
        model_class: SQLAlchemy model class whose table to create
        
    Returns:
        bool: True if successful (table exists or was created), False on error
    """
    try:
        table_name = model_class.__tablename__
        
        if not table_exists(table_name):
            logger.info(f"Creating table {table_name}")
            model_class.__table__.create(db.engine)
            return True
        else:
            logger.debug(f"Table {table_name} already exists")
            return True
    except Exception as e:
        logger.error(f"Error creating table for {model_class.__name__}: {str(e)}")
        return False 

def get_columns_for_table(table_name):
    """
    Get column information for a specific table
    
    Args:
        table_name: Name of the table to examine
        
    Returns:
        list: List of column information dictionaries, each containing:
            - name: Column name
            - type: Column type
            - nullable: Whether column can be null
            - default: Default value of the column
            - primary_key: Whether column is part of primary key
    """
    try:
        inspector = inspect(db.engine)
        if not table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist, cannot get columns")
            return []
        
        columns = inspector.get_columns(table_name)
        return columns
    except Exception as e:
        logger.error(f"Error getting columns for table {table_name}: {str(e)}")
        return []

def add_column_if_not_exists(table_name, column_name, column_type):
    """
    Add a column to a table if it doesn't already exist
    
    Args:
        table_name: Name of the table to modify
        column_name: Name of the column to add
        column_type: SQLAlchemy type object for the new column
        
    Returns:
        bool: True if successful (column exists or was added), False on error
    """
    try:
        # Check if table exists
        if not table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist, cannot add column")
            return False
            
        # Get existing columns
        existing_columns = get_columns_for_table(table_name)
        existing_column_names = [col['name'] for col in existing_columns]
        
        # Add column if it doesn't exist
        if column_name not in existing_column_names:
            logger.info(f"Adding column {column_name} to table {table_name}")
            column_type_str = str(column_type).replace("()", "")
            
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_str}"
            db.engine.execute(sql)
            return True
        else:
            logger.debug(f"Column {column_name} already exists in table {table_name}")
            return True
    except Exception as e:
        logger.error(f"Error adding column {column_name} to table {table_name}: {str(e)}")
        return False 