"""
Authentication Routes Module
Handles user login, registration, and logout functionality
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models.user import User
from db import db
from werkzeug.security import check_password_hash

# Create authentication blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login requests"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('login.html')
            
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Log in the user
            login_user(user)
            flash('Login successful!', 'success')
            # If AI Module is selected and user is admin, redirect to AI dashboard
            ai_module = request.form.get('ai_module')
            if ai_module and user.is_admin:
                return redirect(url_for('main.ai_admin_dashboard'))
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        salary = request.form.get('salary', 0)
        
        # Convert salary to float, default to 0 if not a valid number
        try:
            salary = float(salary)
        except ValueError:
            salary = 0
            
        # Validate input
        if not name or not email or not password:
            flash('Please fill in all required fields', 'error')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('register.html')
            
        # Create new user
        new_user = User(name=name, email=email, password=password, salary=salary)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login')) 