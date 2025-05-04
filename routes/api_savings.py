"""
Savings API Routes Module
Handles savings and saving transactions operations via API endpoints
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from typing import Dict, Any, List

from models import Saving, SavingTransaction
from db import db

# Create savings API blueprint
savings_api = Blueprint('savings_api', __name__, url_prefix='/api/savings')


@savings_api.route('/', methods=['GET'])
@login_required
def get_savings():
    """Get all savings for the current user"""
    try:
        # Get all savings for the current user
        savings = Saving.query.filter_by(user_id=current_user.id).all()
        
        # Format savings as dictionaries
        savings_list = [saving.to_dict() for saving in savings]
        
        return jsonify({
            'status': 'success',
            'count': len(savings_list),
            'savings': savings_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_savings(user_id):
    """Get all savings for a specific user"""
    try:
        # Security check: Only allow current user to access their own savings
        if user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), 403
        
        # Get all savings for the specified user
        savings = Saving.query.filter_by(user_id=user_id).all()
        
        # Format savings as dictionaries
        savings_list = [saving.to_dict() for saving in savings]
        
        return jsonify({
            'status': 'success',
            'count': len(savings_list),
            'savings': savings_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/', methods=['POST'])
@login_required
def add_saving():
    """Add a new saving goal"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'target_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        try:
            # Check if it's a recurring saving
            is_recurring = data.get('is_recurring', False)
            
            # If recurring, validate required recurring fields
            if is_recurring:
                # If we have a target date, recurring amount will be calculated automatically
                if not data.get('target_date') and not data.get('recurring_amount'):
                    return jsonify({
                        'status': 'error',
                        'message': 'For recurring savings without a target date, recurring_amount is required'
                    }), 400
                
                if not data.get('recurring_frequency'):
                    return jsonify({
                        'status': 'error',
                        'message': 'For recurring savings, recurring_frequency is required'
                    }), 400
                
                # Validate frequency
                valid_frequencies = ['monthly', 'quarterly', 'yearly']
                if data['recurring_frequency'] not in valid_frequencies:
                    return jsonify({
                        'status': 'error',
                        'message': f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}"
                    }), 400
            
            # Create new saving
            saving = Saving(
                name=data['name'],
                target_amount=float(data['target_amount']),
                user_id=current_user.id,
                current_amount=float(data.get('current_amount', 0)),
                target_date=data.get('target_date'),
                is_recurring=is_recurring,
                recurring_amount=data.get('recurring_amount'),
                recurring_frequency=data.get('recurring_frequency')
            )
            
            # Add saving to database
            db.session.add(saving)
            db.session.flush()  # Flush to get the ID
            
            # Create the first bill for recurring saving if needed
            first_bill = None
            if is_recurring:
                # Create first bill (due in the current month or next month depending on the day)
                first_bill = saving.create_bill_for_recurring_saving(first_bill=True)
                if first_bill:
                    db.session.add(first_bill)
            
            # Commit all changes
            db.session.commit()
            
            response_data = {
                'status': 'success',
                'message': 'Saving goal created successfully',
                'saving': saving.to_dict()
            }
            
            # Add bill info to response if created
            if first_bill:
                response_data['bill_created'] = True
                response_data['bill_id'] = first_bill.id
                response_data['next_bill_due'] = first_bill.due_date.isoformat()
            
            # Return saving data
            return jsonify(response_data), 201
        except ValueError as ve:
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/<int:saving_id>', methods=['GET'])
@login_required
def get_saving(saving_id):
    """Get details of a specific saving goal"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'saving': saving.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/<int:saving_id>', methods=['PUT'])
@login_required
def update_saving(saving_id):
    """Update an existing saving goal"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        # Get data from request
        data = request.get_json()
        
        # Check if we're changing recurring status
        was_recurring = saving.is_recurring
        will_be_recurring = data.get('is_recurring', was_recurring)
        
        # Update fields if provided
        if 'name' in data:
            saving.name = data['name']
            
        if 'target_amount' in data:
            saving.target_amount = float(data['target_amount'])
            
        if 'current_amount' in data:
            saving.current_amount = float(data['current_amount'])
            
        if 'target_date' in data:
            if data['target_date']:
                try:
                    if isinstance(data['target_date'], str):
                        saving.target_date = datetime.fromisoformat(data['target_date'].replace('Z', '+00:00'))
                    else:
                        saving.target_date = data['target_date']
                except ValueError:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }), 400
            else:
                saving.target_date = None
        
        # Initialize bill variable
        new_bill = None
        
        # If updating recurring status
        if 'is_recurring' in data:
            saving.is_recurring = data['is_recurring']
            
            # Update recurring attributes if needed
            if saving.is_recurring:
                # Validate required recurring fields
                if not data.get('target_date') and not data.get('recurring_amount') and not saving.target_date:
                    return jsonify({
                        'status': 'error',
                        'message': 'For recurring savings without a target date, recurring_amount is required'
                    }), 400
                
                if not data.get('recurring_frequency') and not saving.recurring_frequency:
                    return jsonify({
                        'status': 'error',
                        'message': 'For recurring savings, recurring_frequency is required'
                    }), 400
                
                if 'recurring_amount' in data:
                    saving.recurring_amount = float(data['recurring_amount'])
                
                if 'recurring_frequency' in data:
                    valid_frequencies = ['monthly', 'quarterly', 'yearly']
                    if data['recurring_frequency'] not in valid_frequencies:
                        return jsonify({
                            'status': 'error',
                            'message': f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}"
                        }), 400
                    saving.recurring_frequency = data['recurring_frequency']
                
                # Create a new bill if newly set to recurring
                if not was_recurring:
                    # Create first bill 
                    new_bill = saving.create_bill_for_recurring_saving(first_bill=True)
                    if new_bill:
                        db.session.add(new_bill)
        
        # Save changes
        db.session.commit()
        
        response_data = {
            'status': 'success',
            'message': 'Saving goal updated successfully',
            'saving': saving.to_dict()
        }
        
        # Add bill info to response if created
        if new_bill:
            response_data['bill_created'] = True
            response_data['bill_id'] = new_bill.id
            response_data['next_bill_due'] = new_bill.due_date.isoformat()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/<int:saving_id>', methods=['DELETE'])
@login_required
def delete_saving(saving_id):
    """Delete a saving goal"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        # Delete from database (cascade will delete associated transactions, bills, and any related expenses)
        db.session.delete(saving)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Saving goal deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/<int:saving_id>/transactions', methods=['GET'])
@login_required
def get_saving_transactions(saving_id):
    """Get all transactions for a specific saving goal"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        # Get limit parameter if provided
        limit = request.args.get('limit', default=None, type=int)
        
        # Get transactions
        transactions = saving.get_transactions(limit=limit)
        
        # Format transactions as dictionaries
        transactions_list = [tx.to_dict() for tx in transactions]
        
        return jsonify({
            'status': 'success',
            'count': len(transactions_list),
            'transactions': transactions_list,
            'saving': saving.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/<int:saving_id>/transactions', methods=['POST'])
@login_required
def add_saving_transaction(saving_id):
    """Add a new transaction to a saving goal"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if 'amount' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: amount'
            }), 400
        
        try:
            # Convert string date to datetime object if provided
            date_value = None
            if 'date' in data and data['date']:
                try:
                    from datetime import datetime
                    # Convert ISO format date string to datetime object
                    date_value = datetime.strptime(data['date'], '%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid date format. Use YYYY-MM-DD format.'
                    }), 400
            
            # Add transaction
            transaction = saving.add_transaction(
                amount=float(data['amount']),
                user_id=current_user.id,
                date=date_value,  # Pass the converted datetime object or None
                description=data.get('description'),
                create_expense=data.get('create_expense', False)
            )
            
            # Commit to database
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Transaction added successfully',
                'transaction': transaction.to_dict(),
                'saving': saving.to_dict()
            }), 201
            
        except ValueError as ve:
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/<int:saving_id>/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_saving_transaction(saving_id, transaction_id):
    """Delete a transaction from a saving goal"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        # Delete transaction
        success = saving.delete_transaction(transaction_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Transaction not found or does not belong to this saving goal'
            }), 404
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Transaction deleted successfully',
            'saving': saving.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/make-recurring/<int:saving_id>', methods=['POST'])
@login_required
def make_saving_recurring(saving_id):
    """Convert a regular saving goal to a recurring one"""
    try:
        # Find saving by ID and ensure it belongs to current user
        saving = Saving.query.filter_by(
            id=saving_id, 
            user_id=current_user.id
        ).first()
        
        if not saving:
            return jsonify({
                'status': 'error',
                'message': 'Saving goal not found'
            }), 404
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not saving.target_date and not data.get('recurring_amount'):
            return jsonify({
                'status': 'error',
                'message': 'For recurring savings without a target date, recurring_amount is required'
            }), 400
            
        if not data.get('recurring_frequency'):
            return jsonify({
                'status': 'error',
                'message': 'recurring_frequency is required for recurring savings'
            }), 400
        
        try:
            # Update saving to be recurring
            saving.is_recurring = True
            
            # Set recurring amount if provided
            if 'recurring_amount' in data:
                saving.recurring_amount = float(data['recurring_amount'])
            
            valid_frequencies = ['monthly', 'quarterly', 'yearly']
            if data['recurring_frequency'] not in valid_frequencies:
                return jsonify({
                    'status': 'error',
                    'message': f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}"
                }), 400
                
            saving.recurring_frequency = data['recurring_frequency']
            
            # Create the first bill
            new_bill = saving.create_bill_for_recurring_saving(first_bill=True)
            
            # Add bill to database if created
            if new_bill:
                db.session.add(new_bill)
            
            # Save changes
            db.session.commit()
            
            response_data = {
                'status': 'success',
                'message': 'Saving goal converted to recurring',
                'saving': saving.to_dict()
            }
            
            # Add bill info to response if created
            if new_bill:
                response_data['bill_created'] = True
                response_data['bill_id'] = new_bill.id
                response_data['next_bill_due'] = new_bill.due_date.isoformat()
            
            return jsonify(response_data), 200
            
        except ValueError as ve:
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@savings_api.route('/calculate-emi', methods=['POST'])
@login_required
def calculate_emi():
    """Calculate the EMI amount for a recurring saving"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['target_amount', 'target_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        try:
            # Parse input values
            target_amount = float(data['target_amount'])
            current_amount = float(data.get('current_amount', 0))
            
            # Parse target date
            if data['target_date']:
                try:
                    if isinstance(data['target_date'], str):
                        target_date = datetime.fromisoformat(data['target_date'].replace('Z', '+00:00'))
                    else:
                        target_date = data['target_date']
                except ValueError:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }), 400
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Target date is required for EMI calculation'
                }), 400
            
            frequency = data.get('frequency', 'monthly')
            
            # Validate frequency
            valid_frequencies = ['monthly', 'quarterly', 'yearly']
            if frequency not in valid_frequencies:
                return jsonify({
                    'status': 'error',
                    'message': f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}"
                }), 400
            
            # Calculate EMI
            from dateutil.relativedelta import relativedelta
            import math
            
            # Calculate months between now and target date
            now = datetime.utcnow()
            
            # Check if target date is in the past
            if now >= target_date:
                return jsonify({
                    'status': 'error',
                    'message': 'Target date must be in the future'
                }), 400
            
            # Calculate months remaining
            delta = relativedelta(target_date, now)
            months_remaining = delta.years * 12 + delta.months
            if delta.days > 0:
                months_remaining += 1
                
            # Ensure at least one month
            months_remaining = max(1, months_remaining)
            
            # Calculate number of payments based on frequency
            if frequency == 'monthly':
                num_payments = months_remaining
            elif frequency == 'quarterly':
                num_payments = max(1, months_remaining // 3)
            elif frequency == 'yearly':
                num_payments = max(1, months_remaining // 12)
            else:
                num_payments = months_remaining
            
            # Calculate amount needed to reach target
            amount_needed = target_amount - current_amount
            
            # Calculate EMI (divide remaining amount by number of payments)
            emi = math.ceil(amount_needed / num_payments)
            
            return jsonify({
                'status': 'success',
                'emi_amount': emi,
                'months_remaining': months_remaining,
                'number_of_payments': num_payments,
                'amount_needed': amount_needed
            }), 200
            
        except ValueError as ve:
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 