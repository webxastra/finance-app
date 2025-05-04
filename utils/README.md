# Utilities Package

This package contains utility modules for the Finance App.

## JSON Utilities

The `json_utils.py` module provides essential functionality for handling JSON serialization, particularly focusing on NumPy data types that are not natively serializable by Flask's jsonify function.

### Key Components

1. **NumpyJSONEncoder**:
   - A custom JSONEncoder that extends Flask's JSONEncoder
   - Handles various numpy data types and converts them to standard Python types
   - Applied globally to all Flask routes via `app.json_encoder = NumpyJSONEncoder` in app.py

2. **convert_numpy_types(obj)**:
   - Utility function that recursively converts numpy types in any Python object
   - Works with integers, floats, arrays, dictionaries, and lists
   - Handles special cases like numpy string types

3. **safe_jsonify(*args, **kwargs)**:
   - A drop-in replacement for Flask's jsonify function
   - Ensures all data is properly converted before JSON serialization
   - Available globally as `app.safe_jsonify` and also overrides the default `Flask.jsonify`

### Usage

All routes should automatically benefit from these utilities without any additional code changes due to the global configuration in app.py. However, for explicit handling of numpy types (especially in complex nested data structures), you can use:

```python
from utils.json_utils import safe_jsonify

@app.route('/some-route')
def some_function():
    data = get_data_with_numpy_types()
    return safe_jsonify(data)
```

### Why This Matters

This package was created to solve JSON serialization issues with numpy types when building API responses. Without proper handling, Flask's default jsonify function would raise errors like "Object of type 'int64' is not JSON serializable" or "Object of type 'float32' is not JSON serializable" when encountering numpy types. 