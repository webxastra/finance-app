"""
Application Configuration Module

This module defines configuration settings for different environments:
- Development: Local development environment with debug features enabled
- Testing: Used for automated tests with a separate test database
- Production: Optimized for deployment with secure settings

The configuration class to use is selected based on the FLASK_DEBUG environment 
variable. If not specified, it defaults to '0' (production mode).

Each configuration class inherits from BaseConfig to ensure consistent
shared settings across all environments.
"""

import os
from typing import Dict, Any


class BaseConfig:
    """
    Base configuration class with common settings shared across all environments.
    
    All other environment-specific configuration classes inherit from this class
    to ensure consistent base settings.
    
    Attributes:
        SECRET_KEY (str): Secret key for securing sessions and tokens
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Disable SQLAlchemy modification tracking
        EXPRESS_API_URL (str): URL for the Express API service
    """
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API endpoints
    EXPRESS_API_URL = os.environ.get('EXPRESS_API_URL', 'http://localhost:8000/api')

    # Common SQLAlchemy connection settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }


class DevelopmentConfig(BaseConfig):
    """
    Development environment configuration with debugging enabled.
    
    This configuration is optimized for local development with debug features,
    SQLAlchemy query logging, and a local SQLite database by default.
    
    Attributes:
        DEBUG (bool): Enable debug mode
        SQLALCHEMY_DATABASE_URI (str): Database connection string
        SQLALCHEMY_ECHO (bool): Enable SQL query logging
    """
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///financeapp.db')
    
    # Enable SQL query logging in development
    SQLALCHEMY_ECHO = True
    
    def __init__(self):
        """Initialize development-specific settings."""
        super().__init__()
        # Add SQLite-specific options if using SQLite
        if 'sqlite' in self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_ENGINE_OPTIONS = dict(self.SQLALCHEMY_ENGINE_OPTIONS)
            self.SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'check_same_thread': False}


class TestingConfig(BaseConfig):
    """
    Testing environment configuration with separate test database.
    
    Used for automated tests with a dedicated database and testing-specific
    settings like disabled CSRF protection for easier API testing.
    
    Attributes:
        TESTING (bool): Enable testing mode
        DEBUG (bool): Enable debug mode
        SQLALCHEMY_DATABASE_URI (str): Test database connection string
        WTF_CSRF_ENABLED (bool): Disable CSRF protection for testing
    """
    
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///test_financeapp.db')
    
    # Disable CSRF protection in testing for API testing ease
    WTF_CSRF_ENABLED = False
    
    def __init__(self):
        """Initialize testing-specific settings."""
        super().__init__()
        # Add SQLite-specific options if using SQLite
        if 'sqlite' in self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_ENGINE_OPTIONS = dict(self.SQLALCHEMY_ENGINE_OPTIONS)
            self.SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'check_same_thread': False}


class ProductionConfig(BaseConfig):
    """
    Production environment configuration with secure settings.
    
    Optimized for deployment with enhanced security settings like
    secure session cookies and disabled debug mode.
    
    Attributes:
        DEBUG (bool): Disable debug mode
        SQLALCHEMY_DATABASE_URI (str): Production database connection string
        SESSION_COOKIE_SECURE (bool): Ensure HTTPS for session cookies
        REMEMBER_COOKIE_SECURE (bool): Ensure HTTPS for remember cookies
        SESSION_COOKIE_HTTPONLY (bool): Protect cookies from JavaScript access
    """
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    
    # Ensure HTTPS for session cookies in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    def __init__(self):
        """Initialize production-specific settings."""
        super().__init__()
        # Add PostgreSQL-specific options for production
        if self.SQLALCHEMY_DATABASE_URI and 'postgresql' in self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_ENGINE_OPTIONS = dict(self.SQLALCHEMY_ENGINE_OPTIONS)
            self.SQLALCHEMY_ENGINE_OPTIONS['pool_size'] = 10
            self.SQLALCHEMY_ENGINE_OPTIONS['max_overflow'] = 20


# Configuration dictionary mapping environment names to config classes
config: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}


def get_config():
    """
    Get the appropriate configuration class based on environment.
    
    Determines which configuration class to use based on the FLASK_DEBUG
    environment variable. If set to '1', uses development configuration.
    If set to '0' or not set, uses production configuration.
    
    Returns:
        config class: The configuration class for the current environment
    """
    flask_debug = os.environ.get('FLASK_DEBUG', '0')
    
    if flask_debug == '1':
        return config['development']()
    elif os.environ.get('TESTING', '').lower() == 'true':
        return config['testing']()
    else:
        return config['production']()
