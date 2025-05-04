"""
Bills API Routes Module
Handles bill operations via API endpoints
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from db import db
from models.bill import Bill, FREQUENCIES
from models.expense import Expense
from models.saving import Saving

# Create bills API blueprint
bills_api = Blueprint('bills_api', __name__, url_prefix='/api/bills')


@bills_api.route('/', methods=['GET'])
@login_required
def get_bills():
    """Get all bills for the current user"""
    try:
        # Get all bills for the current user
        bills = Bill.query.filter_by(user_id=current_user.id).all()
        
        # Format bills as dictionaries
        bills_list = [bill.to_dict() for bill in bills]
        
        return jsonify({
            'status': 'success',
            'count': len(bills_list),
            'bills': bills_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bills_api.route('/', methods=['POST'])
@login_required
def add_bill():
    """Add a new bill"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category', 'amount', 'due_date', 'frequency']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
                
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({
                    'status': 'error', 
                    'message': 'Amount must be greater than zero'
                }), 400
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid amount format'
            }), 400
            
        # Validate frequency
        if data['frequency'] not in FREQUENCIES:
            return jsonify({
                'status': 'error',
                'message': f"Invalid frequency. Must be one of: {', '.join(FREQUENCIES)}"
            }), 400
            
        try:
            # Create new bill
            bill = Bill(
                name=data['name'],
                category=data['category'],
                amount=amount,
                due_date=data['due_date'],
                frequency=data['frequency'],
                user_id=current_user.id,
                description=data.get('description')
            )
            
            # Add bill to database
            db.session.add(bill)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Bill added successfully',
                'bill': bill.to_dict()
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


@bills_api.route('/upcoming', methods=['GET'])
@login_required
def get_upcoming_bills():
    """Get upcoming bills for the current user"""
    try:
        # Get all unpaid bills for the current user
        bills = Bill.query.filter_by(user_id=current_user.id, is_paid=False).all()
        
        # Filter for upcoming bills (due within 7 days)
        upcoming_bills = [bill.to_dict() for bill in bills if bill.is_upcoming()]
        
        return jsonify({
            'status': 'success',
            'count': len(upcoming_bills),
            'upcoming_bills': upcoming_bills
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bills_api.route('/<int:bill_id>', methods=['GET'])
@login_required
def get_bill(bill_id):
    """Get details of a specific bill"""
    try:
        # Find bill by ID and ensure it belongs to current user
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
        
        if not bill:
            return jsonify({
                'status': 'error',
                'message': 'Bill not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'bill': bill.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bills_api.route('/<int:bill_id>', methods=['PUT'])
@login_required
def update_bill(bill_id):
    """Update an existing bill"""
    try:
        # Find bill by ID and ensure it belongs to current user
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
        
        if not bill:
            return jsonify({
                'status': 'error',
                'message': 'Bill not found'
            }), 404
        
        # Get data from request
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            bill.name = data['name']
            
        if 'category' in data:
            bill.category = data['category']
            
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({
                        'status': 'error', 
                        'message': 'Amount must be greater than zero'
                    }), 400
                bill.amount = amount
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid amount format'
                }), 400
            
        if 'due_date' in data:
            if data['due_date']:
                try:
                    if isinstance(data['due_date'], str):
                        bill.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                    else:
                        bill.due_date = data['due_date']
                except ValueError:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }), 400
                    
        if 'frequency' in data:
            if data['frequency'] not in FREQUENCIES:
                return jsonify({
                    'status': 'error',
                    'message': f"Invalid frequency. Must be one of: {', '.join(FREQUENCIES)}"
                }), 400
            bill.frequency = data['frequency']
            
        if 'description' in data:
            bill.description = data['description']
            
        # Save changes
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Bill updated successfully',
            'bill': bill.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bills_api.route('/<int:bill_id>', methods=['DELETE'])
@login_required
def delete_bill(bill_id):
    """Delete a bill"""
    try:
        # Find bill by ID and ensure it belongs to current user
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
        
        if not bill:
            return jsonify({
                'status': 'error',
                'message': 'Bill not found'
            }), 404
        
        # Delete from database
        db.session.delete(bill)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Bill deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bills_api.route('/<int:bill_id>/pay', methods=['POST'])
@login_required
def pay_bill(bill_id):
    """Mark a bill as paid"""
    try:
        # Find bill by ID and ensure it belongs to current user
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
        
        if not bill:
            return jsonify({
                'status': 'error',
                'message': 'Bill not found'
            }), 404
        
        # Check if bill is already paid
        if bill.is_paid:
            return jsonify({
                'status': 'error',
                'message': 'Bill is already paid'
            }), 400
        
        # Mark bill as paid
        bill.mark_as_paid()
        
        # Create expense for the bill and update savings goal if linked
        try:
            # Create new expense
            expense = Expense(
                amount=bill.amount,
                category=f"Bills - {bill.category}",
                date=datetime.utcnow(),
                user_id=current_user.id,
                description=f"Payment for {bill.name}"
            )
            
            db.session.add(expense)
            
            # Update the linked saving goal if this is a saving-related bill
            saving_updated = False
            next_bill = None
            
            if bill.saving_id:
                # Get the linked saving goal
                saving = Saving.query.get(bill.saving_id)
                
                if saving:
                    # Add transaction to the saving goal
                    saving.add_transaction(
                        amount=bill.amount,
                        user_id=current_user.id,
                        date=datetime.utcnow(),
                        description=f"Payment via bill: {bill.name}",
                        bill_id=bill.id
                    )
                    
                    saving_updated = True
                    
                    # Check if the goal is completed
                    if saving.is_completed():
                        # Goal completed, no more bills needed
                        response_data = {
                            'status': 'success',
                            'message': 'Bill paid and saving goal completed!',
                            'bill': bill.to_dict(),
                            'expense_id': expense.id,
                            'saving_updated': True,
                            'saving_completed': True,
                            'saving': saving.to_dict()
                        }
                    else:
                        # Goal not completed, generate next bill if recurring
                        if bill.frequency != 'one-time':
                            next_bill = bill.generate_next_bill()
                            if next_bill:
                                db.session.add(next_bill)
            else:
                # If this is a regular bill (not linked to a saving goal)
                # and it's recurring, generate the next one
                if bill.frequency != 'one-time':
                    next_bill = bill.generate_next_bill()
                    if next_bill:
                        db.session.add(next_bill)
            
            db.session.commit()
            
            response_data = {
                'status': 'success',
                'message': 'Bill marked as paid and expense created',
                'bill': bill.to_dict(),
                'expense_id': expense.id
            }
            
            # Add saving info if updated
            if saving_updated:
                response_data['saving_updated'] = True
                response_data['saving'] = saving.to_dict()
            
            # Add next bill info if created
            if next_bill:
                response_data['next_bill_created'] = True
                response_data['next_bill'] = next_bill.to_dict()
            
            return jsonify(response_data), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Error processing payment: {str(e)}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 