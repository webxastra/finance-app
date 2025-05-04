"""
Saving Transaction Model Module

Defines the SavingTransaction class for tracking individual contributions to savings goals.
Each transaction represents money added or removed from a saving goal.
Includes relationships to savings, users, expenses, and bills.
"""

from datetime import datetime
from typing import Optional, Union, Dict, Any
from db import db


class SavingTransaction(db.Model):
    """
    SavingTransaction model for storing contributions to savings goals
    
    Attributes:
        id: Unique identifier for the transaction
        amount: Monetary amount of the transaction (positive for contributions, negative for withdrawals)
        date: When the transaction occurred
        description: Optional description of the transaction
        created_at: When the transaction record was created in the system
        saving_id: Reference to the saving goal this transaction belongs to
        user_id: Reference to the user who created this transaction
        expense_id: Optional reference to an expense entry (if funds were used for an expense)
        bill_id: Optional reference to a bill (if this transaction was from a bill payment)
    """
    
    __tablename__ = 'saving_transactions'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationships
    saving_id = db.Column(db.Integer, db.ForeignKey('savings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=True)
    
    def __init__(self, 
                 amount: float, 
                 saving_id: int, 
                 user_id: int, 
                 date: Optional[datetime] = None, 
                 description: Optional[str] = None, 
                 expense_id: Optional[int] = None, 
                 bill_id: Optional[int] = None):
        """
        Initialize a new saving transaction
        
        Args:
            amount: Transaction amount (positive for contributions, negative for withdrawals)
            saving_id: ID of the associated saving goal
            user_id: ID of the user who made the transaction
            date: Date of the transaction (defaults to current date/time)
            description: Optional description of what the transaction was for
            expense_id: Optional ID of associated expense (for tracking source of funds)
            bill_id: Optional ID of associated bill (for recurring savings)
        """
        self.amount = float(amount)
        self.saving_id = saving_id
        self.user_id = user_id
        self.date = date or datetime.utcnow()
        self.description = description
        self.expense_id = expense_id
        self.bill_id = bill_id
    
    def __repr__(self) -> str:
        """String representation of SavingTransaction object"""
        return f"<SavingTransaction ${self.amount:.2f} for saving_id={self.saving_id}>"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert transaction to dictionary for API responses
        
        Returns:
            Dictionary representation of the transaction
        """
        return {
            'id': self.id,
            'amount': float(self.amount),
            'date': self.date.isoformat(),
            'description': self.description,
            'saving_id': self.saving_id,
            'user_id': self.user_id,
            'expense_id': self.expense_id,
            'bill_id': self.bill_id,
            'created_at': self.created_at.isoformat()
        } 