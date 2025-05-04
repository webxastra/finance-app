"""
Expense Model Module

Defines the Expense class for tracking financial transactions.
Includes fields for amount, category, description, and date.
Supports AI-powered automatic categorization.
"""

from datetime import datetime
from typing import Optional, Union, Dict, Any
from db import db
from sqlalchemy.orm import relationship


class Expense(db.Model):
    """
    Expense model for financial transaction tracking
    
    Attributes:
        id: Unique identifier for the expense
        amount: Monetary amount of the expense
        category: Category classification (e.g., Food, Transport, Entertainment)
        description: Optional detailed description of the expense
        date: When the expense occurred
        created_at: When the expense record was created in the system
        auto_categorized: Whether this expense was categorized automatically by AI
        categorization_confidence: AI confidence score for the assigned category
        user_id: Reference to the user who created this expense
        auto_categorization_explanation: Explanation of the AI categorization decision
        saving_transactions: Collection of saving transactions related to this expense
    """
    
    __tablename__ = 'expenses'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI categorization metadata
    auto_categorized = db.Column(db.Boolean, default=False)
    categorization_confidence = db.Column(db.Float, nullable=True)
    
    # Foreign key relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship with SavingTransaction
    saving_transactions = relationship("SavingTransaction", backref="expense", cascade="all, delete-orphan", lazy="dynamic")
    
    def __init__(self, 
                 amount: float, 
                 category: str, 
                 date: Union[datetime, str], 
                 user_id: int, 
                 description: Optional[str] = None, 
                 auto_categorized: bool = False, 
                 categorization_confidence: Optional[float] = None):
        """
        Initialize a new expense transaction
        
        Args:
            amount: Monetary amount of the expense (positive float)
            category: Category classification (e.g., Food, Transport)
            date: Date when the expense occurred
            user_id: ID of the user who created the expense
            description: Optional description of what the expense was for
            auto_categorized: Whether the expense was auto-categorized by AI
            categorization_confidence: Confidence score of AI categorization (0-1)
        """
        self.amount = float(amount)
        self.category = category
        
        # Convert string dates to datetime objects if needed
        if isinstance(date, str):
            self.date = datetime.strptime(date, "%Y-%m-%d")
        else:
            self.date = date
            
        self.user_id = user_id
        self.description = description
        self.auto_categorized = auto_categorized
        self.categorization_confidence = categorization_confidence
    
    def __repr__(self) -> str:
        """String representation of the Expense"""
        return f"<Expense ${self.amount:.2f} ({self.category})>"
        
    def to_dict(self) -> dict:
        """
        Convert expense to dictionary for API responses
        
        Returns:
            Dictionary representation of the expense
        """
        return {
            'id': self.id,
            'amount': float(self.amount),
            'category': self.category,
            'description': self.description,
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id,
            'auto_categorized': self.auto_categorized,
            'categorization_confidence': self.categorization_confidence
        } 