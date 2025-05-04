"""
Models Package

This package contains all database models used in the application.
Centralizes model importing to prevent circular dependencies.
Provides direct access to model classes via the models package.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime as dt
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()

# Import models after db is defined to avoid circular imports
from models.expense import Expense
from models.saving import Saving
from models.saving_transaction import SavingTransaction
from models.bill import Bill
from models.income import Income
from models.user import User
from models.ai_correction import AICorrection
