"""
Income API Routes Module
Handles income operations via API endpoints
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.income import Income
from models.user import User
from db import db
from datetime import datetime

# Create income API blueprint
income_api = Blueprint('income_api', __name__, url_prefix='/api/income')


@income_api.route('/', methods=['GET'])
@login_required
def get_income():
    """Get all income entries for the current user"""
    try:
        # Get all income entries for the current user
        incomes = Income.query.filter_by(user_id=current_user.id).all()
        
        # Convert to dictionary format
        income_list = [income.to_dict() for income in incomes]
        
        return jsonify({
            'status': 'success',
            'incomes': income_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@income_api.route('/current-month', methods=['GET'])
@login_required
def get_current_month_income():
    """Get income for the current month or default salary"""
    try:
        # Get current month and year
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year
        
        # Get user's default salary
        user = User.query.get(current_user.id)
        default_salary = user.salary if user else 0
        
        # Get income entries for the current month
        current_month_incomes = Income.query.filter_by(
            user_id=current_user.id,
            month=current_month,
            year=current_year
        ).all()
        
        # Calculate total income for the current month
        total_income = sum(income.amount for income in current_month_incomes)
        
        return jsonify({
            'status': 'success',
            'total_income': total_income,
            'default_salary': default_salary,
            'month': current_month,
            'year': current_year,
            'incomes': [income.to_dict() for income in current_month_incomes]
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@income_api.route('/', methods=['POST'])
@login_required
def add_income():
    """Add a new income entry"""
    try:
        data = request.get_json()
        
        # Create new income entry
        new_income = Income(
            amount=data.get('amount'),
            month=data.get('month'),
            year=data.get('year'),
            user_id=current_user.id,
            source=data.get('source', 'Salary'),
            description=data.get('description')
        )
        
        # Add to database
        db.session.add(new_income)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Income added successfully',
            'income': new_income.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@income_api.route('/<int:income_id>', methods=['PUT'])
@login_required
def update_income(income_id):
    """Update an existing income entry"""
    try:
        # Find the income entry
        income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
        
        if not income:
            return jsonify({
                'status': 'error',
                'message': 'Income entry not found'
            }), 404
        
        # Update income entry
        data = request.get_json()
        if 'amount' in data:
            income.amount = float(data['amount'])
        if 'source' in data:
            income.source = data['source']
        if 'month' in data:
            income.month = data['month']
        if 'year' in data:
            income.year = data['year']
        if 'description' in data:
            income.description = data['description']
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Income updated successfully',
            'income': income.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@income_api.route('/<int:income_id>', methods=['DELETE'])
@login_required
def delete_income(income_id):
    """Delete an income entry"""
    try:
        # Find the income entry
        income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
        
        if not income:
            return jsonify({
                'status': 'error',
                'message': 'Income entry not found'
            }), 404
        
        # Delete the income entry
        db.session.delete(income)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Income deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@income_api.route('/user/update-default-salary', methods=['POST'])
@login_required
def update_default_salary():
    """Update user's default monthly salary"""
    try:
        data = request.get_json()
        salary = data.get('salary')
        
        if salary is None:
            return jsonify({
                'status': 'error',
                'message': 'Salary value is required'
            }), 400
        
        # Update user's salary
        user = User.query.get(current_user.id)
        user.salary = float(salary)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Default salary updated successfully',
            'salary': user.salary
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 