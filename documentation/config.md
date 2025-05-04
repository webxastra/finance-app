# config.py

## File Path
`/config.py`

## Description
Configuration module for the Finance App that defines settings for different environments (development, testing, production). The module uses a class-based approach with inheritance to ensure consistent settings across environments.

## Components

### Classes

#### `BaseConfig`
- **Description:** Base configuration class with common settings shared across all environments
- **Attributes:**
  - `SECRET_KEY`: Secret key for securing sessions and tokens (from env or default)
  - `SQLALCHEMY_TRACK_MODIFICATIONS`: Disabled to improve performance
  - `EXPRESS_API_URL`: URL for the Express API service
  - `SQLALCHEMY_ENGINE_OPTIONS`: Connection settings for SQLAlchemy

#### `DevelopmentConfig(BaseConfig)`
- **Description:** Development environment configuration with debugging enabled
- **Attributes:**
  - `DEBUG`: Enabled for development
  - `SQLALCHEMY_DATABASE_URI`: Database connection string (defaults to SQLite)
  - `SQLALCHEMY_ECHO`: Enabled to log SQL queries

#### `TestingConfig(BaseConfig)`
- **Description:** Testing environment configuration used for automated tests
- **Attributes:**
  - `TESTING`: Enabled for testing mode
  - `DEBUG`: Enabled for debugging during tests
  - `SQLALCHEMY_DATABASE_URI`: Test database connection string
  - `WTF_CSRF_ENABLED`: Disabled for easier API testing

#### `ProductionConfig(BaseConfig)`
- **Description:** Production environment configuration with secure settings
- **Attributes:**
  - `DEBUG`: Disabled for production
  - `SQLALCHEMY_DATABASE_URI`: Production database connection string
  - `SESSION_COOKIE_SECURE`: Enabled to ensure HTTPS for cookies
  - `REMEMBER_COOKIE_SECURE`: Enabled to ensure HTTPS for remember cookies
  - `SESSION_COOKIE_HTTPONLY`: Enabled to protect cookies from JavaScript access

### Functions

#### `get_config()`
- **Description:** Returns the appropriate configuration class based on environment
- **Returns:** Configuration class for the current environment
- **Details:** 
  - Uses the FLASK_ENV environment variable to determine which config to use
  - Defaults to 'development' if FLASK_ENV is not set or invalid

### Variables

#### `config`
- **Type:** Dict[str, Any]
- **Description:** Dictionary mapping environment names to config classes
- **Keys:**
  - 'development': DevelopmentConfig
  - 'testing': TestingConfig
  - 'production': ProductionConfig
  - 'default': DevelopmentConfig

## Usage

The configuration is typically loaded in the application factory:

```python
def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    # ...
    return app
```

Environment variables can be used to override default configuration:
- `FLASK_ENV`: Set to 'development', 'testing', or 'production'
- `SECRET_KEY`: Override the secret key (required in production)
- `DATABASE_URL`: Override the database connection string
- `TEST_DATABASE_URL`: Override the test database connection string
- `EXPRESS_API_URL`: Override the Express API URL 

## Related Files

- [app.py](./app.md) - Application entry point that uses the configuration
- [.env.example](../.env.example) - Template for environment variables
- [db.py](./db.md) - Database configuration using these settings

## Navigation

- [Back to Documentation Index](./README.md)
- [Application Documentation](./app.md)
- [Database Documentation](./db.md) 