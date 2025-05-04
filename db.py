"""
Database Module - SQLAlchemy Instance

This module creates a single SQLAlchemy instance that can be imported throughout 
the application. This pattern prevents circular imports when models reference 
each other and follows the Flask application factory pattern.

The SQLAlchemy instance is created here without binding it to a specific Flask
application. During application initialization, the Flask app will call 
db.init_app() to bind the database to the app.

This approach allows models to import the db instance without needing to import
the Flask application, avoiding circular dependencies.

Example usage in models:
```python
from db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ...
```

Example initialization in app:
```python
from flask import Flask
from db import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)
```
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without binding to app
# This allows models to import the db instance without creating circular imports
db = SQLAlchemy() 