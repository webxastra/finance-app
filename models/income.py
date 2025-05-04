"""
Income Model Module

Defines the Income class for tracking monthly income entries.
Each income entry represents money received in a specific month and year.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from db import db


class Income(db.Model):
    """
    Income model for tracking monthly income entries
    
    Attributes:
        id: Unique identifier for the income entry
        amount: Monetary amount received
        source: Source of the income (e.g., Salary, Freelance, Investments)
        month: Month number when income was received (1-12 for Jan-Dec)
        year: Year when income was received
        description: Optional detailed description
        created_at: When the income record was created in the system
        user_id: Reference to the user who received this income
    """
    
    __tablename__ = 'incomes'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False, default="Salary")
    month = db.Column(db.Integer, nullable=False)  # 1-12 for Jan-Dec
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __init__(self, 
                 amount: float, 
                 month: int, 
                 year: int, 
                 user_id: int, 
                 source: str = "Salary", 
                 description: Optional[str] = None):
        """
        Initialize a new income entry
        
        Args:
            amount: Monetary amount received
            month: Month number (1-12 for Jan-Dec)
            year: Year (e.g., 2023)
            user_id: ID of the user who received the income
            source: Source of income (e.g., Salary, Freelance)
            description: Optional description with additional details
        """
        self.amount = float(amount)
        self.source = source
        
        # Validate month range
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        self.month = month
        self.year = year
        self.user_id = user_id
        self.description = description
    
    def __repr__(self) -> str:
        """String representation of Income object"""
        return f"<Income ${self.amount:.2f} from {self.source} for {self.month}/{self.year}>"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert income entry to dictionary for API responses
        
        Returns:
            Dictionary representation of the income entry
        """
        return {
            'id': self.id,
            'amount': float(self.amount),
            'source': self.source,
            'month': self.month,
            'year': self.year,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }
        
    def get_month_name(self) -> str:
        """
        Get the month name for this income entry
        
        Returns:
            Name of the month (e.g., 'January')
        """
        months = [
            'January', 'February', 'March', 'April', 
            'May', 'June', 'July', 'August', 
            'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1] 