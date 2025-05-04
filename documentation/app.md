# app.py

## File Path
`/app.py`

## Description
Main entry point for the Finance App application. This file initializes the Flask application, configures all necessary components, registers blueprints, sets up database connections, initializes the AI system, and runs the server.

## Components

### Functions

#### `configure_logging(app)`
- **Description:** Configures logging for the application with both file-based and console logging.
- **Parameters:** `app` (Flask application instance)
- **Returns:** Configured Flask application instance
- **Details:** 
  - Creates logs directory in instance/logs
  - Sets up log rotation (10MB max file size)
  - Configures different log levels for file (INFO) and console (DEBUG/INFO)
  - Enables SQL query logging in development mode

#### `create_app(config_name=None)`
- **Description:** Application factory function that creates and configures the Flask app.
- **Parameters:** `config_name` (optional) - Name of the configuration to use
- **Returns:** Configured Flask application instance
- **Details:**
  - Loads configuration based on FLASK_ENV
  - Configures custom JSON encoding for numpy types
  - Initializes database connection
  - Sets up Flask-Migrate for database migrations
  - Configures Flask-Login for user authentication
  - Registers error handlers and blueprints

#### `initialize_database(app)`
- **Description:** Initializes the database and ensures all required tables exist.
- **Parameters:** `app` (Flask application instance)
- **Details:**
  - Rolls back any uncommitted transactions
  - Verifies required tables exist
  - Creates missing tables
  - Specifically verifies AI Correction table

#### `initialize_ai_system(app)`
- **Description:** Sets up the AI expense categorization system.
- **Parameters:** `app` (Flask application instance)
- **Details:**
  - Creates directory for AI data
  - Initializes AI trainer
  - Loads existing model or trains initial model

#### `register_error_handlers(app)`
- **Description:** Registers error handlers for common HTTP error codes.
- **Parameters:** `app` (Flask application instance)
- **Details:**
  - Handles 404 (Not Found)
  - Handles 500 (Internal Server Error)
  - Handles 403 (Forbidden)
  - Returns JSON for API requests, HTML for regular requests

#### `register_blueprints(app)`
- **Description:** Registers all blueprints for the application.
- **Parameters:** `app` (Flask application instance)
- **Details:** Registers the following blueprints:
  - main: Main web pages
  - auth: Authentication (login, registration)
  - api: General API endpoints
  - expenses_api: Expense management API
  - savings_api: Savings management API
  - bills_api: Bill management API
  - income_api: Income management API

### Error Handlers

#### `page_not_found(error)`
- **Description:** Handles 404 errors (Page/Resource not found)
- **Returns:** JSON response for API requests, HTML page for web requests

#### `internal_server_error(error)`
- **Description:** Handles 500 errors (Internal server errors)
- **Returns:** JSON response for API requests, HTML page for web requests

#### `forbidden(error)`
- **Description:** Handles 403 errors (Forbidden access)
- **Returns:** JSON response for API requests, HTML page for web requests

## Usage
The application is typically run using:
```python
from app import create_app
app = create_app()

if __name__ == '__main__':
    app.run()
```

Or via gunicorn in production:
```
gunicorn "app:create_app()" 
```

## Related Files

- [config.py](./config.md) - Configuration settings used by the application
- [db.py](./db.md) - Database initialization
- [routes/](./routes/README.md) - API and web route blueprints
- [models/](./models/README.md) - Database models
- [ai_modules/](./ai_modules/README.md) - AI expense categorization

## Navigation

- [Back to Documentation Index](./README.md)
- [Configuration Documentation](./config.md)
- [Database Documentation](./db.md) 