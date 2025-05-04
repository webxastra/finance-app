"""
Utilities Package

This package contains utility modules for the Finance App,
providing shared functionality across different modules.
"""

# Database utilities
from utils.db_utils import (
    table_exists, 
    create_table_if_not_exists,
    get_columns_for_table,
    add_column_if_not_exists
)

# JSON handling utilities
from utils.json_utils import (
    NumpyJSONEncoder,
    convert_numpy_types,
    safe_jsonify,
    deserialize_json
)

# Export all utilities
__all__ = [
    # Database utilities
    'table_exists',
    'create_table_if_not_exists',
    'get_columns_for_table',
    'add_column_if_not_exists',
    
    # JSON utilities
    'NumpyJSONEncoder',
    'convert_numpy_types',
    'safe_jsonify',
    'deserialize_json'
] 