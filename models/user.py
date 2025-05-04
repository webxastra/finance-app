"""
User Model Module
Defines the User class for handling user accounts and authentication.
Includes methods for password management and user representation.
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import Optional
from db import db


class User(db.Model, UserMixin):
    """
    User model for storing user account information and authentication
    
    Attributes:
        id: Unique identifier for the user
        name: User's full name
        email: User's email address (must be unique)
        password_hash: Securely hashed password (never store plain text)
        salary: User's monthly default salary amount
        created_at: When the user account was created
        is_admin: Indicates whether the user is an admin
        
    Relationships:
        expenses: All expenses created by this user
        savings: All savings goals created by this user
        bills: All bills managed by this user
        incomes: All income entries recorded by this user
    """
    
    __tablename__ = 'users'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    salary = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships with other models
    expenses = db.relationship('Expense', backref='author', lazy=True)
    savings = db.relationship('Saving', backref='user', lazy=True)
    bills = db.relationship('Bill', backref='user', lazy=True)
    incomes = db.relationship('Income', backref='user', lazy=True)
    
    def __init__(self, name: str, email: str, password: str, salary: float = 0.0):
        """
        Initialize a new user account
        
        Args:
            name: User's full name
            email: User's email address (must be unique)
            password: Plain text password (will be hashed)
            salary: User's monthly salary amount (default 0.0)
        """
        self.name = name
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.salary = float(salary)
    
    def __repr__(self) -> str:
        """String representation of User object"""
        return f"<User {self.email}>"
    
    def set_password(self, password: str) -> None:
        """
        Set a new password (hash it first)
        
        Args:
            password: New password in plain text
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Check if password matches the hash
        
        Args:
            password: Password to check
            
        Returns:
            Boolean indicating if password matches
        """
        return check_password_hash(self.password_hash, password) 