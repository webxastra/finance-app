"""
Expenses API Routes Module
Handles expense CRUD operations via API endpoints
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.expense import Expense
from db import db
from datetime import datetime
from sqlalchemy import desc

# Create expenses API blueprint
expenses_api = Blueprint('expenses_api', __name__, url_prefix='/api/expenses')


@expenses_api.route('/', methods=['GET'])
@login_required
def get_expenses():
    """Get all expenses for the current user"""
    try:
        # Get query parameters for filtering
        category = request.args.get('category')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', default=100, type=int)
        
        # Base query
        query = Expense.query.filter_by(user_id=current_user.id)
        
        # Apply filters if provided
        if category:
            query = query.filter_by(category=category)
            
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Expense.date >= start_date)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Expense.date <= end_date)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400
        
        # Order by date (newest first) and limit results
        expenses = query.order_by(desc(Expense.date)).limit(limit).all()
        
        # Convert to dictionary format
        expenses_data = [expense.to_dict() for expense in expenses]
        
        return jsonify({
            'status': 'success',
            'count': len(expenses_data),
            'expenses': expenses_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@expenses_api.route('/', methods=['POST'])
@login_required
def add_expense():
    """Add a new expense for the current user"""
    try:
        # Get data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'category', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Parse date
        try:
            date = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Create new expense
        expense = Expense(
            amount=float(data['amount']),
            category=data['category'],
            date=date,
            user_id=current_user.id,
            description=data.get('description'),
            auto_categorized=data.get('auto_categorized', False),
            categorization_confidence=data.get('categorization_confidence')
        )
        
        # Add to database
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Expense added successfully',
            'expense': expense.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@expenses_api.route('/<int:expense_id>', methods=['GET'])
@login_required
def get_expense(expense_id):
    """Get a specific expense by ID"""
    try:
        # Find expense by ID and ensure it belongs to current user
        expense = Expense.query.filter_by(
            id=expense_id, 
            user_id=current_user.id
        ).first()
        
        if not expense:
            return jsonify({
                'status': 'error',
                'message': 'Expense not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'expense': expense.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@expenses_api.route('/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    """Update an existing expense"""
    try:
        # Find expense by ID and ensure it belongs to current user
        expense = Expense.query.filter_by(
            id=expense_id, 
            user_id=current_user.id
        ).first()
        
        if not expense:
            return jsonify({
                'status': 'error',
                'message': 'Expense not found'
            }), 404
        
        # Get data from request
        data = request.get_json()
        
        # Update fields if provided
        if 'amount' in data:
            expense.amount = float(data['amount'])
            
        if 'category' in data:
            expense.category = data['category']
            
        if 'description' in data:
            expense.description = data['description']
            
        if 'date' in data:
            try:
                expense.date = datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Expense updated successfully',
            'expense': expense.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@expenses_api.route('/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        # Find expense by ID and ensure it belongs to current user
        expense = Expense.query.filter_by(
            id=expense_id, 
            user_id=current_user.id
        ).first()
        
        if not expense:
            return jsonify({
                'status': 'error',
                'message': 'Expense not found'
            }), 404
        
        # Delete from database
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Expense deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@expenses_api.route('/categories', methods=['GET'])
@login_required
def get_expense_categories():
    """Get all unique expense categories for the current user"""
    try:
        # Query for unique categories
        categories = db.session.query(Expense.category)\
            .filter_by(user_id=current_user.id)\
            .distinct()\
            .all()
        
        # Extract category names from result tuples
        category_list = [category[0] for category in categories]
        
        return jsonify({
            'status': 'success',
            'categories': category_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@expenses_api.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_expenses(user_id):
    """Get all expenses for a specific user ID"""
    try:
        # Security check - users can only access their own expenses
        if user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized to access expenses for this user'
            }), 403
            
        # Get query parameters for filtering
        category = request.args.get('category')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', default=100, type=int)
        
        # Base query
        query = Expense.query.filter_by(user_id=user_id)
        
        # Apply filters if provided
        if category:
            query = query.filter_by(category=category)
            
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Expense.date >= start_date)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Expense.date <= end_date)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400
        
        # Order by date (newest first) and limit results
        expenses = query.order_by(desc(Expense.date)).limit(limit).all()
        
        # Convert to dictionary format
        expenses_data = [expense.to_dict() for expense in expenses]
        
        return jsonify({
            'status': 'success',
            'count': len(expenses_data),
            'expenses': expenses_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 