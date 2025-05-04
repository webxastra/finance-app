"""
JSON Utilities for Flask Application

This module provides utility functions and classes for JSON serialization,
particularly for handling numpy types that are not natively serializable by Flask's jsonify.
"""

import json
import numpy as np
from flask import jsonify as flask_jsonify
from flask.json import JSONEncoder as FlaskJSONEncoder

class NumpyJSONEncoder(FlaskJSONEncoder):
    """
    Custom JSONEncoder for handling numpy types in Flask applications.
    Extends Flask's JSONEncoder to handle various numpy data types.
    """
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int32, np.int64, np.number)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif hasattr(obj, 'dtype') and 'numpy' in str(type(obj)).lower():
            return obj.item()
        return super(NumpyJSONEncoder, self).default(obj)

def convert_numpy_types(obj):
    """
    Convert numpy types in an object to standard Python types for JSON serialization.
    
    Args:
        obj: Any Python object potentially containing numpy types
        
    Returns:
        The object with all numpy types converted to standard Python types
    """
    if isinstance(obj, (np.integer, np.int32, np.int64, np.number)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {convert_numpy_types(key): convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, str) and hasattr(obj, 'dtype') and 'numpy' in str(type(obj)).lower():
        # Handle numpy string types
        return str(obj)
    else:
        return obj

def safe_jsonify(*args, **kwargs):
    """
    Safely jsonify objects with numpy types by converting them first.
    
    This is a drop-in replacement for Flask's jsonify function that handles
    numpy types safely by converting them to standard Python types first.
    
    Args:
        *args: Positional arguments to jsonify
        **kwargs: Keyword arguments to jsonify
        
    Returns:
        A Flask Response object with the JSON-encoded data
    """
    if args and len(args) == 1:
        obj = convert_numpy_types(args[0])
        return flask_jsonify(obj)
    elif kwargs:
        obj = convert_numpy_types(kwargs)
        return flask_jsonify(obj)
    else:
        # Handle multiple positional arguments by converting each one
        args = [convert_numpy_types(arg) for arg in args]
        return flask_jsonify(*args)

def deserialize_json(json_str):
    """
    Deserialize a JSON string into Python objects.
    
    This is a utility function to safely deserialize JSON data into Python objects.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        The deserialized Python object
        
    Raises:
        json.JSONDecodeError: If the JSON string is invalid
    """
    if not json_str:
        return None
        
    if isinstance(json_str, bytes):
        json_str = json_str.decode('utf-8')
        
    return json.loads(json_str) 