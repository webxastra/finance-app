"""
Finance App - Application Entry Point

This module serves as the main entry point for the Finance App application.
It initializes the Flask application, configures all necessary components,
registers blueprints, sets up the database connection, initializes the AI system,
and runs the server.

The application follows a modular structure with blueprints for different components:
- Authentication (auth)
- Main pages (main)
- API endpoints (api, expenses_api, savings_api, bills_api, income_api)

The application uses SQLAlchemy for database operations and Flask-Login for 
user authentication and session management.

An AI system is also initialized for expense categorization.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_migrate import Migrate
from db import db
from config import get_config
from utils.json_utils import NumpyJSONEncoder, convert_numpy_types, safe_jsonify

# Configure application-wide logging
def configure_logging(app):
    """
    Configure logging for the application.
    
    Sets up both file-based and console logging with proper formatting and rotation.
    Log files are stored in the instance/logs directory and rotated when they reach 10MB.
    
    Args:
        app (Flask): Flask application instance to configure logging for
        
    Returns:
        Flask: The configured Flask application instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.instance_path, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up the formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s - [in %(pathname)s:%(lineno)d]'
    )
    
    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'), 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Configure root logger
    app.logger.handlers = []  # Remove default handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Configure SQLAlchemy logging
    if app.debug:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Log startup
    app.logger.info('Finance App starting up')
    
    return app

# Initialize Flask application
def create_app(config_name=None):
    """
    Create and configure the Flask application instance.
    
    This is the application factory function that:
    1. Creates the Flask app
    2. Configures it from the appropriate configuration object
    3. Sets up logging, database, migrations, login management
    4. Registers blueprints and error handlers
    5. Initializes the database and AI system
    
    Args:
        config_name (str, optional): Name of the configuration to use.
            If None, it will be determined from the FLASK_DEBUG environment variable.
            Defaults to None.
            
    Returns:
        Flask: The configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load appropriate configuration based on environment
    config_name = config_name or os.environ.get('FLASK_DEBUG', '0')
    app.config.from_object(get_config())
    
    # Configure logging
    configure_logging(app)
    
    # Configure Flask to use custom JSON encoder for all routes
    app.json_encoder = NumpyJSONEncoder
    
    # Make these utility functions available in the app context
    app.convert_numpy_types = convert_numpy_types
    app.safe_jsonify = safe_jsonify
    
    # Override Flask's jsonify with our safe version
    # This ensures all jsonify calls in the app use the safe version
    Flask.jsonify = safe_jsonify
    
    # Initialize database
    db.init_app(app)
    
    # Setup migrations
    Migrate(app, db)
    
    # Configure login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import models package - after db is initialized
    from models import User, Expense, Bill, SavingTransaction, Saving, Income
    
    # Define user loader function
    @login_manager.user_loader
    def load_user(user_id):
        """
        Load user from database by user ID.
        
        Required by Flask-Login to retrieve User object based on stored user_id.
        
        Args:
            user_id (str): The user ID to load
            
        Returns:
            User: The user object if found, None otherwise
        """
        return User.query.get(int(user_id))
    
    # Register health check endpoint for Docker
    @app.route('/health')
    def health_check():
        """Health check endpoint for Docker container monitoring"""
        try:
            # Check database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return jsonify({"status": "healthy", "database": "connected"}), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy", "error": str(e)}), 500
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables
    with app.app_context():
        initialize_database(app)
        
        # Initialize AI system
        initialize_ai_system(app)
        
    return app

def initialize_database(app):
    """
    Initialize the database and ensure all tables exist.
    
    This function:
    1. Rolls back any uncommitted transactions
    2. Verifies required database tables exist
    3. Creates any missing tables
    4. Verifies the AICorrection table specifically
    
    Args:
        app (Flask): Flask application instance
    """
    # Check for any uncommitted transactions and roll them back
    try:
        app.logger.info("Checking for uncommitted database transactions")
        db.session.rollback()
        app.logger.info("Database session rolled back successfully")
    except Exception as e:
        app.logger.warning(f"Error rolling back database session: {str(e)}")
    
    # Verify database tables
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        app.logger.info(f"Database tables: {tables}")
        
        # Check for required tables
        required_tables = ['users', 'expenses', 'ai_corrections']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            app.logger.warning(f"Missing tables: {missing_tables}")
        else:
            app.logger.info("All required tables exist")
    except Exception as e:
        app.logger.error(f"Error checking database tables: {str(e)}")
            
    # Create all tables
    db.create_all()
    app.logger.info("Database tables created/updated")
    
    # Verify AICorrection table specifically
    try:
        from models.ai_correction import AICorrection
        result = AICorrection.ensure_table_exists()
        app.logger.info(f"AICorrection table check result: {result}")
    except Exception as e:
        app.logger.error(f"Error checking AICorrection table: {str(e)}")

def initialize_ai_system(app):
    """
    Initialize the AI expense categorization system.
    
    This function:
    1. Creates a directory for AI data
    2. Initializes the AI trainer
    3. Loads an existing model or trains an initial model if none exists
    
    Args:
        app (Flask): Flask application instance
    """
    try:
        # Import trainer
        from ai_modules.expense_categorizer.ai_trainer import AITrainer
        
        # Create a directory for AI data in the instance folder
        ai_data_dir = os.path.join(app.instance_path, 'ai')
        os.makedirs(ai_data_dir, exist_ok=True)
        
        # Initialize the trainer
        app.ai_trainer = AITrainer(base_dir=ai_data_dir)
        
        # Load or train initial model
        if not app.ai_trainer.classifier.is_trained:
            # Try to load existing model
            loaded = app.ai_trainer.classifier.load()
            
            # If no model exists, train initial model
            if not loaded:
                app.logger.info("No existing AI model found, training initial model")
                app.ai_trainer.train_initial_model()
        
        app.logger.info("AI expense categorization system initialized")
        
    except Exception as e:
        app.logger.error(f"Error initializing AI system: {str(e)}")
        app.ai_trainer = None

def register_error_handlers(app):
    """
    Register error handlers for the application.
    
    Sets up handlers for common HTTP error codes (404, 500, 403)
    with different responses for API vs HTML requests.
    
    Args:
        app (Flask): Flask application instance
    """
    @app.errorhandler(404)
    def page_not_found(error):
        """
        Handle 404 errors - Page/Resource not found.
        
        Returns JSON for API requests, HTML for regular requests.
        
        Args:
            error: The error object
            
        Returns:
            tuple: Response and status code
        """
        app.logger.warning(f"404 Page not found: {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'message': 'Resource not found'
            }), 404
        return app.render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """
        Handle 500 errors - Internal server error.
        
        Returns JSON for API requests, HTML for regular requests.
        
        Args:
            error: The error object
            
        Returns:
            tuple: Response and status code
        """
        app.logger.error(f"500 Internal Server Error: {str(error)}")
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500
        return app.render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """
        Handle 403 errors - Forbidden access.
        
        Returns JSON for API requests, HTML for regular requests.
        
        Args:
            error: The error object
            
        Returns:
            tuple: Response and status code
        """
        app.logger.warning(f"403 Forbidden: {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'message': 'Access forbidden'
            }), 403
        return app.render_template('errors/403.html'), 403

def register_blueprints(app):
    """
    Register all blueprints for the application.
    
    Imports and registers blueprint modules for different parts of the application:
    - main: Main web pages
    - auth: Authentication (login, registration, etc.)
    - api: General API endpoints
    - expenses_api: API for expense management
    - savings_api: API for savings management
    - bills_api: API for bill management
    - income_api: API for income management
    
    Args:
        app (Flask): Flask application instance
    """
    # Import all blueprints from the routes package
    from routes import main, auth, api, expenses_api, savings_api, bills_api, income_api
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(api)
    app.register_blueprint(expenses_api)
    app.register_blueprint(savings_api)
    app.register_blueprint(bills_api)
    app.register_blueprint(income_api)
    
    # AI/ML module routes
    from ai_modules.expense_categorizer.service import ai_expense
    app.register_blueprint(ai_expense)
    
    app.logger.info("All blueprints registered successfully")

# Create the application instance
app = create_app()

# Run the application when executed directly
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
