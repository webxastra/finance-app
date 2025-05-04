"""
Bill Model Module

Defines the Bill class for tracking recurring and one-time bills.
Includes functionality for payment tracking and generating future bills.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any, List
from db import db
from sqlalchemy.orm import relationship


# Valid bill frequencies
FREQUENCIES = ['monthly', 'quarterly', 'yearly', 'one-time']


class Bill(db.Model):
    """
    Bill model for tracking recurring and one-time bills
    
    Attributes:
        id: Unique identifier for the bill
        name: Descriptive name of the bill
        category: Type of bill (e.g., utilities, rent, subscription)
        amount: Monetary amount due
        due_date: When the bill payment is due
        frequency: How often the bill recurs (monthly, quarterly, yearly, one-time)
        is_paid: Whether the bill has been paid
        payment_date: When the bill was paid (if paid)
        description: Optional detailed description
        created_at: When the bill record was created in the system
        user_id: Reference to the user who owns this bill
        saving_id: Reference to the saving goal associated with this bill (optional)
        transactions: Collection of saving transactions linked to this bill
    """
    
    __tablename__ = 'bills'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Foreign key relationship with Saving (optional)
    saving_id = db.Column(db.Integer, db.ForeignKey('savings.id'), nullable=True)
    
    # Relationship with SavingTransaction
    transactions = relationship("SavingTransaction", backref="bill", cascade="all, delete-orphan", lazy="dynamic")
    
    def __init__(self, 
                 name: str, 
                 category: str, 
                 amount: float, 
                 due_date: Union[datetime, str], 
                 frequency: str, 
                 user_id: int, 
                 description: Optional[str] = None,
                 saving_id: Optional[int] = None):
        """
        Initialize a new bill
        
        Args:
            name: Name/title of the bill
            category: Category of the bill (utilities, rent, etc.)
            amount: Monetary amount due
            due_date: Due date of the bill (datetime or string in ISO format)
            frequency: How often the bill recurs (monthly, quarterly, yearly, one-time)
            user_id: ID of the user who owns the bill
            description: Optional description with additional details
            saving_id: ID of the saving goal associated with this bill (optional)
        
        Raises:
            ValueError: If frequency is not one of the valid options
        """
        self.name = name
        self.category = category
        self.amount = float(amount)
        
        # Handle string date input
        if isinstance(due_date, str):
            try:
                self.due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        else:
            self.due_date = due_date
        
        # Validate frequency
        if frequency not in FREQUENCIES:
            raise ValueError(f"Invalid frequency. Must be one of: {', '.join(FREQUENCIES)}")
        
        self.frequency = frequency
        self.user_id = user_id
        self.description = description
        self.is_paid = False
        self.payment_date = None
        self.saving_id = saving_id
    
    def mark_as_paid(self, payment_date: Optional[datetime] = None) -> None:
        """
        Mark bill as paid
        
        Args:
            payment_date: Date when the bill was paid. Defaults to current time if not provided.
        """
        self.is_paid = True
        self.payment_date = payment_date or datetime.utcnow()
    
    def is_overdue(self) -> bool:
        """
        Check if bill is overdue (due date has passed and bill is unpaid)
        
        Returns:
            Boolean indicating if the bill is overdue
        """
        return not self.is_paid and datetime.utcnow() > self.due_date
    
    def is_upcoming(self, days: int = 7) -> bool:
        """
        Check if bill is due within a specified number of days
        
        Args:
            days: Number of days to consider a bill as upcoming (default: 7)
            
        Returns:
            Boolean indicating if the bill is due soon
        """
        if self.is_paid:
            return False
            
        now = datetime.utcnow()
        return now <= self.due_date <= (now + timedelta(days=days))
    
    def generate_next_bill(self) -> Optional['Bill']:
        """
        Generate the next bill based on frequency
        
        Returns:
            New Bill object for the next billing cycle, or None if one-time bill
        """
        if self.frequency == 'one-time':
            return None
            
        from dateutil.relativedelta import relativedelta
        
        # Calculate next due date based on frequency
        if self.frequency == 'monthly':
            next_due_date = self.due_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            next_due_date = self.due_date + relativedelta(months=3)
        elif self.frequency == 'yearly':
            next_due_date = self.due_date + relativedelta(years=1)
        else:
            return None
            
        # Create new bill with next due date
        return Bill(
            name=self.name,
            category=self.category,
            amount=self.amount,
            due_date=next_due_date,
            frequency=self.frequency,
            user_id=self.user_id,
            description=self.description,
            saving_id=self.saving_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert bill to dictionary for API responses
        
        Returns:
            Dictionary representation of the bill
        """
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'amount': float(self.amount),
            'due_date': self.due_date.isoformat(),
            'frequency': self.frequency,
            'is_paid': self.is_paid,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id,
            'saving_id': self.saving_id,
            'is_overdue': self.is_overdue(),
            'is_upcoming': self.is_upcoming()
        }
    
    def __repr__(self) -> str:
        """String representation of Bill object"""
        status = 'Paid' if self.is_paid else 'Unpaid'
        return f"<Bill {self.name}: ${self.amount:.2f} ({status})>" 