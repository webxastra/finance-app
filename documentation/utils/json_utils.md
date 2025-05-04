# JSON Utilities

## File Path
`/utils/json_utils.py`

## Description
This module provides custom JSON handling functionality for the Finance App, particularly focusing on handling NumPy data types in API responses. It ensures proper serialization of numerical data from analytical functions.

## Components

### Classes

#### `NumpyJSONEncoder`
- **Description**: Custom JSON encoder for handling NumPy data types
- **Inherits From**: `flask.json.JSONEncoder`
- **Methods**:
  - `default(obj)`: Converts NumPy types to Python native types

### Functions

#### `convert_numpy_types(obj)`
- **Description**: Recursive function to convert NumPy types to Python native types
- **Parameters**:
  - `obj`: Any Python object that might contain NumPy values
- **Returns**: Object with NumPy types converted to native Python types
- **Details**:
  - Handles NumPy arrays, scalars, and other numeric types
  - Processes nested dictionaries and lists recursively
  - Falls back to original value if not a NumPy type

#### `safe_jsonify(*args, **kwargs)`
- **Description**: Replacement for Flask's `jsonify` that handles NumPy types
- **Parameters**:
  - Same as Flask's `jsonify`
- **Returns**: Flask response with JSON content
- **Details**:
  - Applies `convert_numpy_types` before serialization
  - Uses the custom `NumpyJSONEncoder` for the conversion
  - Maintains the same API as Flask's `jsonify`

## NumPy Type Handling

The module handles the following NumPy types:
- `numpy.integer` (int8, int16, int32, int64, etc.)
- `numpy.floating` (float16, float32, float64, etc.)
- `numpy.ndarray` (converted to Python lists)
- `numpy.bool_` (converted to Python bool)
- `numpy.datetime64` (converted to ISO format string)

## Usage Examples

### Converting NumPy types in data
```python
import numpy as np
from utils.json_utils import convert_numpy_types

# Create a dictionary with NumPy types
data = {
    'value': np.float32(123.45),
    'array': np.array([1, 2, 3]),
    'nested': {
        'integer': np.int64(42)
    }
}

# Convert to Python native types
converted_data = convert_numpy_types(data)
print(converted_data)  # All NumPy types converted to Python types
```

### Using safe_jsonify in routes
```python
from flask import Blueprint
from utils.json_utils import safe_jsonify
import numpy as np

bp = Blueprint('example', __name__)

@bp.route('/data')
def get_data():
    # Data with NumPy types
    data = {
        'values': np.array([1.1, 2.2, 3.3]),
        'count': np.int64(100)
    }
    
    # Will be properly converted and serialized
    return safe_jsonify(data)
```

## Related Files

- [app.py](../app.md) - Application setup using the custom JSON encoder
- [routes/api.py](../routes/api.md) - API routes using safe_jsonify
- [ai_modules/expense_categorizer.md](../ai_modules/expense_categorizer.md) - AI module that returns NumPy types

## Navigation

- [Back to Utils Documentation](./README.md)
- [Back to Main Documentation](../README.md)
- [API Routes Documentation](../routes/api.md) 