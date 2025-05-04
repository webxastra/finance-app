"""
Recurring Transaction Detector Service

This module provides the Flask API endpoints for the recurring transaction 
detector functionality, allowing the frontend to detect and manage recurring expenses.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from .detector import RecurringTransactionDetector
from models.expense import Expense
from db import db
import logging
from datetime import datetime, timedelta
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint for recurring transaction detection
ai_recurring = Blueprint('ai_recurring', __name__, url_prefix='/api/ai/recurring')

# Initialize the detector
detector = RecurringTransactionDetector(
    min_occurrences=2,  # Default: minimum 2 occurrences to be considered recurring
    time_window_days=365,  # Default: look at transactions up to 1 year old
    amount_variance=0.2,  # Default: allow 20% variation in amount
    date_variance_days=7  # Default: allow 7 days variance in timing
)

@ai_recurring.route('/detect', methods=['GET'])
@login_required
def detect_recurring_transactions():
    """
    Detect recurring transactions for the current user
    
    Query parameters:
    - time_window: Number of days to look back (default: 365)
    - min_occurrences: Minimum occurrences required (default: 2)
    - include_transactions: Whether to include transaction details (default: false)
    
    Returns:
    {
        "recurring_transactions": [
            {
                "description": "Netflix Subscription",
                "average_amount": 12.99,
                "frequency_days": 30,
                "frequency_type": "monthly",
                "frequency_name": "Monthly",
                "last_date": "2023-04-15",
                "next_expected_date": "2023-05-15",
                "transaction_count": 6,
                "confidence": 0.85,
                "is_subscription": true,
                "annual_cost": 155.88
            }
        ],
        "total_annual_cost": 155.88,
        "count": 1
    }
    """
    try:
        # Get query parameters
        time_window_days = request.args.get('time_window', default=365, type=int)
        min_occurrences = request.args.get('min_occurrences', default=2, type=int)
        include_transactions = request.args.get('include_transactions', default='false').lower() == 'true'
        
        # Configure detector
        detector.time_window_days = time_window_days
        detector.min_occurrences = min_occurrences
        
        # Get user expenses within the time window
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        
        user_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= cutoff_date
        ).order_by(Expense.date.asc()).all()
        
        # Detect recurring transactions
        recurring_groups = detector.detect_recurring(user_expenses)
        
        # Calculate annual costs
        total_annual_cost = 0
        recurring_data = []
        
        for group in recurring_groups:
            # Calculate annual cost
            annual_cost = detector.predict_annual_cost(group)
            total_annual_cost += annual_cost
            
            # Create response object
            group_data = {
                "description": group["description"],
                "average_amount": group["average_amount"],
                "frequency_days": group["frequency_days"],
                "frequency_type": group["frequency_type"],
                "frequency_name": group["frequency_name"],
                "last_date": group["last_date"],
                "next_expected_date": group["next_expected_date"],
                "transaction_count": group["transaction_count"],
                "confidence": group["confidence"],
                "is_subscription": group["is_subscription"],
                "annual_cost": annual_cost
            }
            
            # Optionally include transaction details
            if include_transactions:
                group_data["transactions"] = group["transactions"]
                
            recurring_data.append(group_data)
        
        # Return results
        return jsonify({
            "recurring_transactions": recurring_data,
            "total_annual_cost": round(total_annual_cost, 2),
            "count": len(recurring_data)
        })
        
    except Exception as e:
        logger.error(f"Error detecting recurring transactions: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@ai_recurring.route('/analyze', methods=['POST'])
@login_required
def analyze_custom_transactions():
    """
    Analyze a custom set of transactions for recurring patterns
    
    Request JSON:
    {
        "transactions": [
            {
                "id": 123,
                "amount": 12.99,
                "date": "2023-01-15",
                "description": "Netflix Subscription"
            }
        ],
        "min_occurrences": 2
    }
    
    Returns:
    {
        "recurring_transactions": [ ... ]  # Same format as detect endpoint
    }
    """
    try:
        data = request.json
        
        if not data or 'transactions' not in data:
            return jsonify({'error': 'Missing transactions data'}), 400
            
        transactions = data.get('transactions', [])
        min_occurrences = data.get('min_occurrences', 2)
        
        # Configure detector
        detector.min_occurrences = min_occurrences
        
        # Detect recurring patterns
        recurring_groups = detector.detect_recurring(transactions)
        
        # Calculate annual costs
        recurring_data = []
        
        for group in recurring_groups:
            annual_cost = detector.predict_annual_cost(group)
            
            group_data = {
                "description": group["description"],
                "average_amount": group["average_amount"],
                "frequency_days": group["frequency_days"],
                "frequency_type": group["frequency_type"],
                "frequency_name": group["frequency_name"],
                "last_date": group["last_date"],
                "next_expected_date": group["next_expected_date"],
                "transaction_count": group["transaction_count"],
                "confidence": group["confidence"],
                "is_subscription": group["is_subscription"],
                "annual_cost": annual_cost,
                "transactions": group["transactions"]
            }
            
            recurring_data.append(group_data)
        
        # Return results
        return jsonify({
            "recurring_transactions": recurring_data
        })
        
    except Exception as e:
        logger.error(f"Error analyzing custom transactions: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@ai_recurring.route('/stats', methods=['GET'])
@login_required
def get_recurring_stats():
    """
    Get statistics about recurring expenses and subscriptions
    
    Returns:
    {
        "total_subscriptions": 5,
        "total_monthly_cost": 125.75,
        "total_annual_cost": 1509.00,
        "top_expenses": [
            {
                "description": "Rent",
                "amount": 1200.00,
                "frequency": "Monthly"
            }
        ],
        "upcoming_payments": [
            {
                "description": "Netflix",
                "amount": 12.99,
                "due_date": "2023-05-15"
            }
        ]
    }
    """
    try:
        # Get recurring transactions
        cutoff_date = datetime.now() - timedelta(days=365)
        
        user_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= cutoff_date
        ).order_by(Expense.date.asc()).all()
        
        # Detect recurring transactions
        recurring_groups = detector.detect_recurring(user_expenses)
        
        # Calculate statistics
        total_monthly_cost = sum(
            group["average_amount"] * (30 / group["frequency_days"]) 
            if group["frequency_days"] > 0 else 0
            for group in recurring_groups
        )
        
        total_annual_cost = sum(
            detector.predict_annual_cost(group) 
            for group in recurring_groups
        )
        
        # Get top expenses (by monthly cost)
        top_expenses = []
        for group in sorted(recurring_groups, 
                           key=lambda x: x["average_amount"] * (30 / x["frequency_days"] if x["frequency_days"] > 0 else 0), 
                           reverse=True)[:5]:
            top_expenses.append({
                "description": group["description"],
                "amount": group["average_amount"],
                "frequency": group["frequency_name"]
            })
        
        # Get upcoming payments in the next 30 days
        upcoming_payments = []
        today = datetime.now()
        for group in recurring_groups:
            next_date = datetime.strptime(group["next_expected_date"], "%Y-%m-%d")
            days_until = (next_date - today).days
            
            if 0 <= days_until <= 30:
                upcoming_payments.append({
                    "description": group["description"],
                    "amount": group["average_amount"],
                    "due_date": group["next_expected_date"],
                    "days_until": days_until
                })
        
        # Sort by days until payment
        upcoming_payments.sort(key=lambda x: x["days_until"])
        
        return jsonify({
            "total_subscriptions": len(recurring_groups),
            "total_monthly_cost": round(total_monthly_cost, 2),
            "total_annual_cost": round(total_annual_cost, 2),
            "top_expenses": top_expenses,
            "upcoming_payments": upcoming_payments
        })
        
    except Exception as e:
        logger.error(f"Error getting recurring stats: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500 