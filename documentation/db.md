# db.py

## File Path
`/db.py`

## Description
This file creates a single SQLAlchemy instance that can be imported throughout the application. It follows the Flask application factory pattern to prevent circular imports when models reference each other.

## Components

### Variables

#### `db`
- **Type:** SQLAlchemy
- **Description:** The SQLAlchemy database instance used across the application
- **Details:**
  - Initialized without being bound to a Flask app
  - Later bound to the app using `db.init_app(app)` during application initialization
  - Used in models for defining tables, relationships and queries

## Usage

### In Models
The db instance is imported in model files to define database tables and relationships:

```python
from db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # ...
```

### In Application Initialization
The db instance is bound to the Flask app during initialization:

```python
from flask import Flask
from db import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    db.init_app(app)
    # ...
    return app
```

### For Database Operations
Common operations using the db instance:

```python
# Create tables
with app.app_context():
    db.create_all()

# Add a new record
db.session.add(new_user)
db.session.commit()

# Query data
users = User.query.all()

# Delete a record
db.session.delete(user)
db.session.commit()
```

## Design Pattern
This file implements the Flask application factory pattern which helps:
1. Prevent circular imports
2. Allow models to be defined separately from the application
3. Make testing easier by allowing different configurations
4. Support creating multiple application instances with different configurations 

## Related Files

- [app.py](./app.md) - Application initialization using the db instance
- [config.py](./config.md) - Database configuration settings
- [models/](./models/README.md) - Database models using this instance

## Navigation

- [Back to Documentation Index](./README.md)
- [Application Documentation](./app.md)
- [Models Documentation](./models/README.md) 