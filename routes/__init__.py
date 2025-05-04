"""
Routes Package
Centralizes all application routes into organized blueprints

This package imports all route modules and exposes their blueprints
to be registered with the Flask application.
"""

# Import blueprints from route modules
from routes.main import main
from routes.auth import auth
from routes.api import api
from routes.api_expenses import expenses_api
from routes.api_savings import savings_api
from routes.api_bills import bills_api
from routes.api_income import income_api

# Export blueprints for Flask app registration
__all__ = ['main', 'auth', 'api', 'expenses_api', 'savings_api', 'bills_api', 'income_api'] 