"""
Main Routes Module
Defines the main page routes for the application
"""

from flask import Blueprint, render_template, redirect, url_for, make_response, flash
from flask_login import login_required, current_user
from models.saving import Saving
from models.expense import Expense
from datetime import datetime
from ai_modules.recurring_detector.detector import RecurringTransactionDetector
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint for main pages
main = Blueprint('main', __name__)

# Helper function to prevent caching of authenticated pages
def no_cache_headers(response):
    """
    Add headers to prevent browser caching of authenticated pages
    
    Args:
        response: Flask response object
        
    Returns:
        Modified response with cache control headers
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@main.route('/')
def index():
    """Home page route - redirects to login if not authenticated"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return redirect(url_for('auth.login'))


@main.route('/home')
@login_required
def home():
    """Dashboard page after login"""
    response = make_response(render_template('home.html'))
    return no_cache_headers(response)


@main.route('/balance')
@login_required
def balance():
    """Balance page showing financial overview"""
    response = make_response(render_template('balance.html'))
    return no_cache_headers(response)


@main.route('/savings')
@login_required
def savings():
    """Savings page showing all savings"""
    # Get all savings for the current user
    user_savings = Saving.query.filter_by(user_id=current_user.id).all()
    
    # Apply no-cache headers to prevent caching of authenticated pages
    response = make_response(render_template('savings.html', savings=user_savings))
    return no_cache_headers(response)


@main.route('/service')
@login_required
def service():
    """Service page showing available services"""
    response = make_response(render_template('service.html'))
    return no_cache_headers(response)


@main.route('/charts')
@login_required
def charts():
    """Charts page for financial visualization"""
    response = make_response(render_template('charts.html'))
    return no_cache_headers(response)


@main.route('/transactions')
@login_required
def transactions():
    """Transactions page showing all financial transactions"""
    response = make_response(render_template('transactions.html'))
    return no_cache_headers(response)


@main.route('/investment')
@login_required
def investment():
    """Investment calculator page"""
    response = make_response(render_template('investment.html'))
    return no_cache_headers(response)


@main.route('/budget')
@login_required
def budget():
    """Budget planning page"""
    response = make_response(render_template('budget.html'))
    return no_cache_headers(response)


@main.route('/bills')
@login_required
def bills():
    """Bills management page"""
    response = make_response(render_template('bills.html'))
    return no_cache_headers(response)


@main.route('/news')
@login_required
def news():
    """Financial news page"""
    response = make_response(render_template('news.html'))
    return no_cache_headers(response)


@main.route('/stock-info')
@login_required
def stock_info():
    """Stock information page"""
    response = make_response(render_template('stock_info.html'))
    return no_cache_headers(response)


@main.route('/stock-prediction')
@login_required
def stock_prediction():
    """Stock prediction page with ML insights"""
    response = make_response(render_template('stock_prediction.html'))
    return no_cache_headers(response)


@main.route('/income')
@login_required
def income_management():
    """Monthly income management page"""
    response = make_response(render_template('income.html'))
    return no_cache_headers(response)


@main.route('/recurring-subscriptions')
@login_required
def recurring_subscriptions():
    """
    Route handler for the recurring subscriptions page.
    Analyzes user transactions to identify recurring payments and subscription patterns.
    """
    try:
        # Get the user's transactions from the database
        user_id = current_user.id
        transactions = Expense.query.filter(
            Expense.user_id == user_id
        ).order_by(Expense.date.desc()).all()
        
        if not transactions:
            flash('No transaction data available to analyze.', 'info')
            return render_template('recurring_subscriptions.html', patterns=[], stats={
                'monthly_subscription_cost': 0,
                'annual_subscription_cost': 0, 
                'total_subscriptions': 0,
                'monthly_recurring_cost': 0,
                'upcoming_payments': [],
                'top_expenses': []
            })
        
        # Convert SQLAlchemy objects to dictionaries for the detector
        transaction_data = []
        for tx in transactions:
            transaction_data.append({
                'date': tx.date,
                'description': tx.description,
                'amount': float(tx.amount),
                'category': tx.category
            })
        
        # Initialize the recurring transaction detector
        detector = RecurringTransactionDetector(
            min_occurrences=2,           # Minimum occurrences to identify a pattern
            time_window_days=365,        # Look at last year of transactions
            amount_variance=0.10,        # Allow 10% variance in amounts
            date_variance_days=3         # Allow 3 days variance in dates
        )
        
        # Detect patterns in transaction data
        patterns = detector.detect_recurring_transactions(transaction_data)
        
        # Get stats about the recurring transactions
        stats = detector.get_stats()
        
        # Calculate total monthly expenses (for percentage calculation)
        current_date = datetime.utcnow()
        current_month = current_date.month
        current_year = current_date.year
        
        # Render the recurring subscriptions template with the detected patterns
        response = make_response(render_template(
            'recurring_subscriptions.html',
            patterns=patterns,
            stats=stats
        ))
        return no_cache_headers(response)
        
    except Exception as e:
        flash(f'Error analyzing recurring transactions: {str(e)}', 'error')
        return render_template('recurring_subscriptions.html', patterns=[], stats={})


@main.route('/admin/ai-training')
@login_required
def ai_admin():
    """AI model management and training dashboard"""
    # Check if user is admin
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template('admin/ai_training.html')


@main.route('/admin/ai')
@login_required
def ai_admin_dashboard():
    """AI Admin Dashboard"""
    # Check if user is admin
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template('admin/ai_dashboard.html') 