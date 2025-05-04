from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any, List
from db import db
from sqlalchemy.orm import relationship
from sqlalchemy import func
from dateutil.relativedelta import relativedelta
import math

"""
Saving Model Module

Defines the Saving class for tracking financial savings goals.
Includes functionality for managing transactions, tracking progress,
and handling recurring savings plans.
"""

class Saving(db.Model):
    """
    Saving model for tracking financial savings goals
    
    Attributes:
        id: Unique identifier for the saving goal
        name: Descriptive name of the goal (e.g., "New Car", "Emergency Fund")
        target_amount: Total amount to be saved
        current_amount: Amount currently saved
        target_date: Optional deadline for achieving the goal
        created_at: When the saving goal was created
        is_recurring: Whether this is a recurring saving with periodic contributions
        recurring_amount: Amount to save in each period (for recurring savings)
        recurring_frequency: How often to contribute (monthly, quarterly, yearly)
        user_id: Reference to the user who owns this saving goal
        transactions: Collection of transactions related to this saving goal
        bills: Collection of bills related to this saving goal
    """
    
    __tablename__ = 'savings'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0.0)
    target_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_amount = db.Column(db.Float, nullable=True)
    recurring_frequency = db.Column(db.String(20), nullable=True)
    
    # Foreign key relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    transactions = relationship("SavingTransaction", backref="saving", cascade="all, delete-orphan", lazy="dynamic")
    bills = relationship("Bill", backref="saving", cascade="all, delete-orphan", lazy="dynamic")
    
    def __init__(self, 
                 name: str, 
                 target_amount: float, 
                 user_id: int, 
                 current_amount: float = 0.0, 
                 target_date: Optional[Union[datetime, str]] = None, 
                 is_recurring: bool = False, 
                 recurring_amount: Optional[float] = None, 
                 recurring_frequency: Optional[str] = None):
        """
        Initialize a new saving goal
        
        Args:
            name: Name of the saving goal
            target_amount: Total amount to save
            user_id: ID of the user who created the goal
            current_amount: Amount already saved (default 0.0)
            target_date: Target completion date (optional)
            is_recurring: Whether this is a recurring saving plan
            recurring_amount: Amount to save periodically
            recurring_frequency: Frequency of saving (monthly, quarterly, yearly)
            
        Raises:
            ValueError: If target_amount is negative or recurring settings are invalid
        """
        if target_amount <= 0:
            raise ValueError("Target amount must be positive")
            
        self.name = name
        self.target_amount = float(target_amount)
        self.current_amount = float(current_amount)
        self.user_id = user_id
        
        # Handle string date input
        if isinstance(target_date, str) and target_date:
            try:
                self.target_date = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        else:
            self.target_date = target_date
        
        # Set recurring attributes
        self.is_recurring = is_recurring
        
        if is_recurring:
            if not recurring_amount or not recurring_frequency:
                raise ValueError("Recurring savings must specify amount and frequency")
                
            self.recurring_amount = float(recurring_amount)
            
            valid_frequencies = ['monthly', 'quarterly', 'yearly']
            if recurring_frequency not in valid_frequencies:
                raise ValueError(f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}")
                
            self.recurring_frequency = recurring_frequency
        else:
            self.recurring_amount = None
            self.recurring_frequency = None
    
    def add_transaction(self, 
                        amount: float, 
                        user_id: int, 
                        date: Optional[datetime] = None, 
                        description: Optional[str] = None, 
                        create_expense: bool = False, 
                        bill_id: Optional[int] = None) -> 'SavingTransaction':
        """
        Add a transaction to this saving goal and update the current amount
        
        Args:
            amount: Amount to add to the saving (positive for contributions, negative for withdrawals)
            user_id: ID of the user making the transaction
            date: Date of the transaction (defaults to now)
            description: Optional description of the transaction
            create_expense: Whether to create an expense record for this transaction
            bill_id: Optional ID of a bill if this is from a recurring saving plan
            
        Returns:
            SavingTransaction object that was created
            
        Raises:
            ValueError: If withdrawal would make balance negative
        """
        from models.saving_transaction import SavingTransaction
        from models.expense import Expense
        
        amount = float(amount)
        
        # Check if withdrawal would make balance negative
        if amount < 0 and (self.current_amount + amount) < 0:
            raise ValueError("Cannot withdraw more than the current amount")
        
        # Create expense if requested
        expense_id = None
        if create_expense and amount > 0:  # Only create expense for positive amounts
            expense = Expense(
                amount=amount,
                category=f"Savings - {self.name}",
                date=date or datetime.utcnow(),
                user_id=user_id,
                description=f"Contribution to {self.name} savings goal"
            )
            db.session.add(expense)
            db.session.flush()  # Flush to get the expense ID
            expense_id = expense.id
        
        # Create transaction
        transaction = SavingTransaction(
            amount=amount,
            saving_id=self.id,
            user_id=user_id,
            date=date,
            description=description,
            expense_id=expense_id,
            bill_id=bill_id
        )
        
        # Update current amount
        self.current_amount += amount
        
        # Add transaction to database session
        db.session.add(transaction)
        
        return transaction
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction from this saving goal and update the current amount
        
        Args:
            transaction_id: ID of the transaction to delete
            
        Returns:
            Boolean indicating success or failure
        """
        from models.saving_transaction import SavingTransaction
        
        # Find the transaction
        transaction = SavingTransaction.query.get(transaction_id)
        
        # Check if transaction exists and belongs to this saving
        if not transaction or transaction.saving_id != self.id:
            return False
        
        # Update current amount
        self.current_amount -= transaction.amount
        
        # If transaction has an associated expense, delete it too
        if transaction.expense_id:
            from models.expense import Expense
            expense = Expense.query.get(transaction.expense_id)
            if expense:
                db.session.delete(expense)
        
        # Delete transaction
        db.session.delete(transaction)
        
        return True
    
    def create_bill_for_recurring_saving(self, first_bill=False) -> Optional['Bill']:
        """
        Create a bill for a recurring saving plan
        
        Args:
            first_bill: Whether this is the first bill (should be due immediately)
        
        Returns:
            Bill object that was created, or None if this is not a recurring saving
        """
        if not self.is_recurring:
            return None
        
        from models.bill import Bill
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        import math
        
        # Auto-calculate recurring amount if target date is set
        if self.target_date:
            # Calculate months between now and target date
            now = datetime.utcnow()
            
            # Calculate months remaining
            if now >= self.target_date:
                # Target date is in the past, set 1 month as default
                months_remaining = 1
            else:
                # Calculate months between now and target date
                delta = relativedelta(self.target_date, now)
                months_remaining = delta.years * 12 + delta.months
                # If we're close to the end of the month and due date is early next month, add a month
                if delta.days > 0:
                    months_remaining += 1
                # Ensure at least one month
                months_remaining = max(1, months_remaining)
            
            # Calculate amount needed to reach target
            amount_needed = self.target_amount - self.current_amount
            
            # If goal is already achieved, don't create new bills
            if amount_needed <= 0:
                return None
                
            # Calculate monthly EMI (divide remaining amount by remaining months)
            emi = math.ceil(amount_needed / months_remaining)
            
            # Update recurring amount
            self.recurring_amount = emi
        
        # Don't create bills if recurring amount is not set
        if not self.recurring_amount:
            return None
        
        # Calculate due date based on frequency
        now = datetime.utcnow()
        
        if first_bill:
            # First bill is due on the same day of the current month (or next month if we're late in the month)
            day = min(now.day, 28)  # Ensure valid day for all months
            if now.day > 20:  # If we're late in the month, first bill is next month
                due_date = now + relativedelta(months=1, day=day)
            else:
                due_date = now.replace(day=day)
        else:
            # Get the date of the first bill (or use now if not calculating a sequence)
            if first_bill == False:  # We're calculating the second bill
                # Start from 1 month after the current date
                base_date = now + relativedelta(months=1)
                day = min(base_date.day, 28)  # Ensure valid day for all months
                
                # Apply frequency from this base date
                if self.recurring_frequency == 'monthly':
                    due_date = base_date + relativedelta(months=1, day=day)
                elif self.recurring_frequency == 'quarterly':
                    due_date = base_date + relativedelta(months=3, day=day)
                elif self.recurring_frequency == 'yearly':
                    due_date = base_date + relativedelta(years=1, day=day)
                else:
                    # Default to one month if frequency is not recognized
                    due_date = base_date + relativedelta(months=1, day=day)
            else:
                # We're calculating a future bill in a sequence
                base_date = first_bill
                day = min(base_date.day, 28)  # Ensure valid day for all months
                
                # Apply frequency from this base date
                if self.recurring_frequency == 'monthly':
                    due_date = base_date + relativedelta(months=1, day=day)
                elif self.recurring_frequency == 'quarterly':
                    due_date = base_date + relativedelta(months=3, day=day)
                elif self.recurring_frequency == 'yearly':
                    due_date = base_date + relativedelta(years=1, day=day)
                else:
                    # Default to one month if frequency is not recognized
                    due_date = base_date + relativedelta(months=1, day=day)
        
        # Create bill
        bill = Bill(
            name=f"Savings - {self.name}",
            category="Savings",
            amount=self.recurring_amount,
            due_date=due_date,
            frequency=self.recurring_frequency,
            user_id=self.user_id,
            description=f"Recurring saving for {self.name}",
            saving_id=self.id  # Link bill to the saving goal
        )
        
        return bill
    
    def get_progress_percentage(self) -> float:
        """
        Calculate the progress percentage towards the saving goal
        
        Returns:
            Float representing the percentage completed (0-100)
        """
        if self.target_amount <= 0:
            return 0
        return min(100, (self.current_amount / self.target_amount) * 100)
    
    def get_transactions(self, limit: Optional[int] = None) -> List['SavingTransaction']:
        """
        Get all transactions for this saving goal
        
        Args:
            limit: Optional limit on number of transactions to return
            
        Returns:
            List of SavingTransaction objects
        """
        from models.saving_transaction import SavingTransaction
        
        query = SavingTransaction.query.filter_by(saving_id=self.id).order_by(SavingTransaction.date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
        
    def get_days_remaining(self) -> Optional[int]:
        """
        Calculate days remaining until the target date
        
        Returns:
            Number of days remaining, or None if no target date
        """
        if not self.target_date:
            return None
            
        remaining = (self.target_date - datetime.utcnow()).days
        return max(0, remaining)
        
    def is_completed(self) -> bool:
        """
        Check if the saving goal has been achieved
        
        Returns:
            Boolean indicating if the current amount equals or exceeds the target
        """
        return self.current_amount >= self.target_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert saving goal to dictionary for API responses
        
        Returns:
            Dictionary representation of the saving goal
        """
        return {
            'id': self.id,
            'name': self.name,
            'target_amount': float(self.target_amount),
            'current_amount': float(self.current_amount),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'created_at': self.created_at.isoformat(),
            'is_recurring': self.is_recurring,
            'recurring_amount': float(self.recurring_amount) if self.recurring_amount else None,
            'recurring_frequency': self.recurring_frequency,
            'user_id': self.user_id,
            'progress_percentage': self.get_progress_percentage(),
            'days_remaining': self.get_days_remaining(),
            'is_completed': self.is_completed()
        }
    
    def __repr__(self) -> str:
        """String representation of Saving object"""
        return f"<Saving {self.name}: ${self.current_amount:.2f}/{self.target_amount:.2f} ({self.get_progress_percentage():.1f}%)>" 