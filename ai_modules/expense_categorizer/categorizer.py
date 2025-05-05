"""
Expense Categorization Model

This module handles the automatic categorization of expenses into predefined categories
using machine learning techniques and natural language processing.
"""

import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score, f1_score
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import logging
import string
from collections import Counter
import traceback
import os
import time
import sys
import json
import pickle
from datetime import datetime
from pathlib import Path
import spacy
import xgboost as xgb
import shap
from sklearn.preprocessing import LabelEncoder

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the correction model for DB lookups
def _import_ai_correction():
    try:
        from models.ai_correction import AICorrection
        from db import db
        return AICorrection, db
    except Exception as e:
        logger.error(f"Could not import AICorrection/db: {e}")
        return None, None

# Add a helper to ExpenseCategorizer to check DB for corrections
def _get_db_correction(self, description, amount=None):
    """Query the database for a matching correction (global, not user-specific)."""
    AICorrection, db = _import_ai_correction()
    if AICorrection is None:
        return None
    try:
        norm_desc = description.strip().lower()
        query = AICorrection.query.filter(
            AICorrection.description.ilike(norm_desc)
        )
        if amount is not None:
            # Try to match amount within a small tolerance
            query = query.filter(db.func.abs(AICorrection.amount - float(amount)) < 0.01)
        correction = query.order_by(AICorrection.created_at.desc()).first()
        return correction
    except Exception as e:
        logger.error(f"DB correction lookup failed: {e}")
        return None

# Set up custom NLTK data directory to avoid permission issues
def setup_nltk_data_dir():
    """Set up a custom NLTK data directory in the user's home directory"""
    # First check environment variable
    nltk_data_env = os.environ.get('NLTK_DATA')
    if nltk_data_env and os.path.exists(nltk_data_env):
        logger.info(f"Using NLTK_DATA env variable: {nltk_data_env}")
        # Clear existing paths and set only this one
        nltk.data.path = [nltk_data_env]
        return nltk_data_env, None
    
    # Add all possible NLTK data directories to the path for comprehensive search
    home_dir = str(Path.home())
    nltk_data_dir = os.path.join(home_dir, 'nltk_data')
    
    # Check for docker-specific paths
    docker_paths = [
        '/app/nltk_data',
        '/usr/local/share/nltk_data',
        '/usr/share/nltk_data'
    ]
    
    # Try docker paths first
    for path in docker_paths:
        if os.path.exists(path):
            logger.info(f"Using existing Docker NLTK data path: {path}")
            nltk.data.path = [path]
            return path, None
    
    # Create directory if it doesn't exist
    if not os.path.exists(nltk_data_dir):
        try:
            os.makedirs(nltk_data_dir)
            os.makedirs(os.path.join(nltk_data_dir, 'corpora'), exist_ok=True)
            logger.info(f"Created custom NLTK data directory at {nltk_data_dir}")
        except Exception as e:
            logger.error(f"Failed to create NLTK data directory: {str(e)}")
    
    # Get conda environment path if available
    conda_env = os.environ.get('CONDA_PREFIX')
    conda_nltk_dir = None
    if conda_env:
        conda_nltk_dir = os.path.join(conda_env, 'nltk_data')
        os.makedirs(os.path.join(conda_nltk_dir, 'corpora'), exist_ok=True)
    
    # Add all potential paths to NLTK's search path
    search_paths = [
        nltk_data_dir,  # Custom user directory
    ]
    
    if conda_nltk_dir:
        search_paths.append(conda_nltk_dir)
        search_paths.append(os.path.join(conda_env, 'share/nltk_data'))
        search_paths.append(os.path.join(conda_env, 'lib/nltk_data'))
    
    # Standard system paths
    search_paths.extend([
        '/usr/share/nltk_data',
        '/usr/local/share/nltk_data',
        '/usr/lib/nltk_data',
        '/usr/local/lib/nltk_data'
    ])
    
    # Set environment variable
    os.environ['NLTK_DATA'] = nltk_data_dir
    
    # Clear existing paths and add ours in priority order
    nltk.data.path = []
    for path in search_paths:
        if os.path.exists(path) and path not in nltk.data.path:
            nltk.data.path.append(path)
            logger.info(f"Added NLTK data path: {path}")
    
    # Only log once to reduce verbosity
    logger.info(f"NLTK search paths configured: {nltk.data.path}")
    
    return nltk_data_dir, conda_nltk_dir

# Set up NLTK data directory
setup_nltk_data_dir()

# Ensure NLTK resources are available
def ensure_nltk_resources():
    """Download required NLTK resources if they aren't already available"""
    # Import at the top to avoid UnboundLocalError
    import nltk
    
    # Get the paths where we'll download resources
    nltk_data_dir, conda_nltk_dir = setup_nltk_data_dir()
    
    required_resources = [
        ('stopwords', 'corpora/stopwords'),
        ('wordnet', 'corpora/wordnet'),
        ('omw-1.4', 'corpora/omw-1.4'),
        ('punkt', 'tokenizers/punkt')
    ]
    
    # Force download resources to both user and conda directories
    for resource_name, resource_path in required_resources:
        logger.info(f"Ensuring NLTK resource '{resource_name}' is available...")
        
        # First - check if it's already accessible
        try:
            nltk.data.find(resource_path)
            logger.info(f"✓ NLTK resource '{resource_name}' already accessible")
            
            # Additional verification for WordNet & OMW
            if resource_name == 'wordnet':
                try:
                    from nltk.corpus import wordnet as wn
                    synsets = wn.synsets('test')
                    if synsets:
                        logger.info(f"✓ WordNet is functioning correctly: found {len(synsets)} synsets for 'test'")
                    else:
                        logger.warning("⚠ WordNet loaded but returned no synsets - will download again")
                        raise LookupError("WordNet verification failed")
                except Exception:
                    logger.warning(f"⚠ WordNet verification failed - will download again")
                    # Fall through to download
            
            # If verification passes, continue to next resource
            continue
        except LookupError:
            logger.info(f"NLTK resource '{resource_name}' not found. Will download...")
        
        # Download to user home directory
        download_success = False
        try:
            logger.info(f"Downloading '{resource_name}' to {nltk_data_dir}...")
            nltk.download(resource_name, download_dir=nltk_data_dir, quiet=False)
            logger.info(f"Download to user directory completed")
            download_success = True
        except Exception as e:
            logger.error(f"Failed to download to user directory: {str(e)}")
        
        # Also download to conda environment if available
        if conda_nltk_dir:
            try:
                logger.info(f"Also downloading '{resource_name}' to conda env: {conda_nltk_dir}")
                nltk.download(resource_name, download_dir=conda_nltk_dir, quiet=False)
                logger.info(f"Download to conda directory completed")
                download_success = True
            except Exception as e:
                logger.error(f"Failed to download to conda directory: {str(e)}")
        
        # If download failed through nltk, try direct system approach for critical resources
        if not download_success and resource_name in ['wordnet', 'omw-1.4']:
            try:
                logger.info("Attempting direct download through system Python...")
                import subprocess
                
                # Try both directories
                for target_dir in [nltk_data_dir, conda_nltk_dir]:
                    if not target_dir:
                        continue
                        
                    cmd = f"python -c \"import nltk; nltk.download('{resource_name}', download_dir='{target_dir}')\""
                    subprocess.call(cmd, shell=True)
                    
                    # Try to create symbolic links to ensure directory structure is correct
                    if resource_name == 'wordnet':
                        src = os.path.join(target_dir, 'corpora/wordnet')
                        dest = os.path.join(target_dir, 'corpora/omw-1.4/wordnet')
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        try:
                            if not os.path.exists(dest) and os.path.exists(src):
                                os.symlink(src, dest)
                                logger.info(f"Created symlink from {src} to {dest}")
                        except Exception as e:
                            logger.error(f"Failed to create symlink: {str(e)}")
                
                download_success = True
            except Exception as e:
                logger.error(f"Direct download failed: {str(e)}")
        
        # Final verification - try to use the resource
        try:
            nltk.data.find(resource_path)
            logger.info(f"✓ Successfully verified access to {resource_name}")
            
            # Special verification for WordNet
            if resource_name == 'wordnet':
                try:
                    from nltk.corpus import wordnet as wn
                    synsets = wn.synsets('test')
                    if synsets:
                        logger.info(f"✓ WordNet is now functioning correctly")
                    else:
                        logger.warning("⚠ WordNet still not functioning correctly")
                except Exception as e:
                    logger.warning(f"⚠ WordNet still not functioning correctly: {str(e)}")
            
        except LookupError as e:
            logger.error(f"❌ Failed to access {resource_name} after download attempts: {str(e)}")
            if resource_name in ['wordnet', 'omw-1.4']:
                logger.error(f"WordNet or OMW access failed - lemmatization may be limited")
            elif resource_name == 'stopwords':
                logger.error(f"Stopwords access failed - will use fallback stopword list")
    
    # Reload all modules that use NLTK resources to ensure they use the new paths
    try:
        from importlib import reload
        import nltk.corpus
        reload(nltk.corpus)
        logger.info("Reloaded NLTK corpus module")
    except Exception as e:
        logger.error(f"Failed to reload NLTK modules: {str(e)}")

# Call the function to ensure resources
ensure_nltk_resources()

# Define main expense categories and their subcategories
CATEGORY_HIERARCHY = {
    "Food & Dining": [
        "Groceries", 
        "Restaurants",
        "Fast Food",
        "Coffee Shops",
        "Delivery",
        "Bars & Alcohol",
        "Food Subscriptions"
    ],
    "Transportation": [
        "Gas & Fuel",
        "Public Transportation",
        "Ride Sharing",
        "Parking",
        "Car Maintenance",
        "Car Insurance",
        "Car Payments",
        "Tolls",
        "Bicycle"
    ],
    "Housing": [
        "Mortgage/Rent",
        "Property Taxes",
        "HOA Fees",
        "Home Insurance",
        "Home Maintenance",
        "Home Improvement",
        "Lawn & Garden",
        "Home Services",
        "Furniture",
        "Home Supplies"
    ],
    "Utilities": [
        "Electricity",
        "Water",
        "Gas",
        "Internet",
        "Phone",
        "Cable/Streaming",
        "Waste Management"
    ],
    "Healthcare": [
        "Health Insurance",
        "Doctor Visits",
        "Dental Care",
        "Vision Care",
        "Prescriptions",
        "Medical Equipment",
        "Therapy & Treatments"
    ],
    "Entertainment": [
        "Movies & Events",
        "Games",
        "Music",
        "Books & Magazines",
        "Hobbies",
        "Sports & Recreation",
        "Streaming Services",
        "Concerts"
    ],
    "Shopping": [
        "Clothing",
        "Electronics",
        "Household Items",
        "Personal Items",
        "Online Purchases",
        "Department Stores",
        "Sports Equipment",
        "Beauty Products"
    ],
    "Education": [
        "Tuition",
        "Books & Supplies",
        "Courses",
        "Student Loans",
        "Training",
        "Educational Software"
    ],
    "Personal Care": [
        "Hair & Beauty",
        "Spa & Massage",
        "Gym & Fitness",
        "Personal Hygiene",
        "Health Products"
    ],
    "Travel": [
        "Flights",
        "Hotels",
        "Rental Cars",
        "Cruises",
        "Vacation Activities",
        "Travel Insurance",
        "Vacation Packages"
    ],
    "Investments": [
        "Stocks",
        "Bonds",
        "Mutual Funds",
        "Retirement",
        "Real Estate",
        "Cryptocurrency",
        "Savings"
    ],
    "Gifts & Donations": [
        "Presents",
        "Charity",
        "Religious Donations",
        "Fundraising",
        "Gift Cards"
    ],
    "Insurance": [
        "Life Insurance",
        "Health Insurance",
        "Auto Insurance",
        "Home Insurance",
        "Disability Insurance",
        "Pet Insurance"
    ],
    "Taxes": [
        "Income Tax",
        "Property Tax",
        "Vehicle Tax",
        "Tax Preparation",
        "Tax Payments"
    ],
    "Miscellaneous": [
        "Bank Fees",
        "Credit Card Fees",
        "Shipping",
        "Professional Fees",
        "Legal Services",
        "Membership Fees",
        "Pet Expenses",
        "Unidentified"
    ]
}

class FallbackLemmatizer:
    """
    A robust fallback lemmatizer that can be used if NLTK's WordNetLemmatizer fails.
    Implements basic stemming rules for English words.
    """
    
    def __init__(self):
        # Common English lemmatization rules (suffix -> replacement)
        self.rules = {
            # Plural forms
            'ies': 'y',       # categories -> category
            'es': '',         # boxes -> box
            's': '',          # cats -> cat
            
            # Verb forms
            'ing': '',        # running -> run
            'ed': '',         # walked -> walk
            'ied': 'y',       # studied -> study
            'ying': 'y',      # studying -> study
            'ies': 'y',       # applies -> apply
            
            # Adjective forms
            'est': '',        # biggest -> big
            'er': '',         # bigger -> big
            
            # Noun forms
            'ment': '',       # payment -> pay
            'ence': 'e',      # difference -> differ
            'ance': '',       # performance -> perform
            'ity': '',        # activity -> active
            'ism': '',        # capitalism -> capital
            'tion': 't',      # creation -> create
            'sion': 'd',      # expansion -> expand
        }
        
        # Exception list for words that shouldn't be stemmed
        self.exceptions = {
            'business', 'news', 'paris', 'this', 'was', 'is', 'has', 'gas', 'bus',
            'series', 'species', 'analysis', 'basis', 'crisis', 'thesis',
            'status', 'virus', 'bonus', 'minus', 'campus', 'texas', 'vegas'
        }
        
        # Common irregular forms mapping
        self.irregular_forms = {
            'are': 'be',
            'were': 'be',
            'is': 'be',
            'am': 'be',
            'was': 'be',
            'being': 'be',
            'been': 'be',
            'had': 'have',
            'has': 'have',
            'having': 'have',
            'does': 'do',
            'did': 'do',
            'doing': 'do',
            'done': 'do',
            'went': 'go',
            'going': 'go',
            'goes': 'go',
            'gone': 'go',
            'made': 'make',
            'making': 'make',
            'makes': 'make',
            'said': 'say',
            'saying': 'say',
            'says': 'say',
            'bought': 'buy',
            'buying': 'buy',
            'buys': 'buy',
            'took': 'take',
            'taking': 'take',
            'takes': 'take',
            'taken': 'take',
        }
        
        # Cache for previously lemmatized words to improve performance
        self.cache = {}
    
    def lemmatize(self, word, pos=None):
        """
        Apply basic lemmatization rules to a word
        
        Args:
            word (str): The word to lemmatize
            pos (str, optional): Part of speech (not used, included for API compatibility)
            
        Returns:
            str: The lemmatized word
        """
        # Handle invalid input
        if not word or not isinstance(word, str):
            return "" if word is None else str(word)
        
        # Convert to lowercase for consistency
        word = word.lower()
        
        # Check cache first
        if word in self.cache:
            return self.cache[word]
        
        # Check exceptions - words that shouldn't be stemmed
        if word in self.exceptions:
            self.cache[word] = word
            return word
            
        # Check irregular forms
        if word in self.irregular_forms:
            self.cache[word] = self.irregular_forms[word]
            return self.irregular_forms[word]
            
        # For very short words, don't apply rules
        if len(word) <= 3:
            self.cache[word] = word
            return word
            
        # Special case for double consonant + 'ing' or 'ed'
        if (word.endswith('ing') and len(word) > 5 and
            word[-4] == word[-5] and word[-4] not in 'aeiou'):
            # running -> run (remove -ning)
            result = word[:-4]
            self.cache[word] = result
            return result
        
        if (word.endswith('ed') and len(word) > 4 and
            word[-3] == word[-4] and word[-3] not in 'aeiou'):
            # stopped -> stop (remove -ped)
            result = word[:-3]
            self.cache[word] = result
            return result
        
        # Try each suffix rule
        original_word = word
        for suffix, replacement in self.rules.items():
            if word.endswith(suffix):
                # Only apply if the stem would be at least 2 chars
                stem_length = len(word) - len(suffix) + len(replacement)
                if stem_length >= 2:
                    word = word[:-len(suffix)] + replacement
                    break
        
        # Only update cache if word was actually changed
        if word != original_word:
            self.cache[original_word] = word
            
        return word

class ExpenseCategorizer:
    """
    A machine learning model for expense categorization.
    Uses natural language processing to categorize expense descriptions
    into predefined spending categories.
    """
    
    def __init__(self, use_detailed_categories=False):
        """
        Initialize the expense categorizer
        
        Args:
            use_detailed_categories (bool): Whether to use detailed subcategories
                                            instead of main categories
        """
        self.model = None
        self.vectorizer = None
        self.categories = list(CATEGORY_HIERARCHY.keys())
        self.nlp = None
        
        # Try to load SpaCy model for better NLP processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded SpaCy model for NER")
        except Exception as e:
            logger.warning(f"Could not load SpaCy model: {str(e)}")
            logger.info("Named Entity Recognition will not be available")
        
        # Try to initialize NLTK lemmatizer, fall back to simple if it fails
        try:
            # First ensure WordNet is properly loaded
            try:
                from nltk.corpus import wordnet as wn
                # Test that WordNet is accessible
                if not wn.synsets('test'):
                    # If no synsets, raise error to trigger fallback
                    raise ImportError("WordNet accessible but not working correctly")
                logger.info("WordNet is accessible for lemmatization")
            except Exception as e:
                logger.warning(f"WordNet access issue: {str(e)}")
                # We'll continue and let the lemmatizer handle errors
            
            # Initialize and test the lemmatizer
            self.lemmatizer = WordNetLemmatizer()
            test_word = self.lemmatizer.lemmatize("testing", pos='v')  # Explicit POS to ensure it's working
            
            if test_word != "test":  # Expected lemma form of "testing" (verb)
                logger.warning(f"Lemmatizer returned unexpected result: {test_word}")
                raise ValueError("Lemmatizer not working correctly")
                
            logger.info("Successfully initialized NLTK WordNetLemmatizer")
                
        except Exception as e:
            logger.warning(f"Could not initialize NLTK lemmatizer: {str(e)}")
            logger.info("Using robust fallback lemmatizer")
            self.lemmatizer = FallbackLemmatizer()
        
        # Try to initialize stopwords, fall back to a basic list if it fails
        try:
            self.stop_words = set(stopwords.words('english'))
            # Add additional financial and transaction-specific stopwords
            financial_stopwords = {
                'payment', 'purchase', 'paid', 'pay', 'transaction', 'receipt', 'invoice',
                'order', 'bill', 'subscription', 'charge', 'amount', 'account', 'credit',
                'debit', 'card', 'cash', 'check', 'transfer', 'balance', 'fee', 'total',
                'expense', 'cost', 'price', 'monthly', 'annual', 'quarterly', 'recurring',
                'purchase', 'bought', 'paid', 'spend', 'spent', 'payment', 'date', 'money'
            }
            self.stop_words.update(financial_stopwords)
        except Exception as e:
            logger.warning(f"Could not load NLTK stopwords: {str(e)}")
            logger.info("Using basic stopword list")
            # Basic English stopwords
            self.stop_words = {
                'a', 'an', 'the', 'and', 'or', 'but', 'if', 'of', 'at', 'by', 
                'for', 'with', 'about', 'to', 'from', 'in', 'on', 'is', 'was', 
                'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
                'did', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 
                'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 
                'those', 'am', 'are', 'will', 'would', 'shall', 'should', 'can', 
                'could', 'may', 'might', 'must', 'ought', 'payment', 'purchase', 
                'paid', 'pay', 'transaction', 'receipt', 'invoice', 'order', 'bill'
            }
        
        self.use_detailed_categories = use_detailed_categories
        self.feature_importances = {}
        self.category_keywords = {}
        self.model_type = "xgboost"  # Default to XGBoost
        self.shap_explainer = None
        self.corrections_data = []
        
        # Path for storing corrections data
        self.corrections_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "user_corrections.json"
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.corrections_path), exist_ok=True)
        
        # Load any existing corrections
        self._load_corrections()
        
        # Detailed categories include all subcategories
        if use_detailed_categories:
            self.categories = []
            for main_category, subcategories in CATEGORY_HIERARCHY.items():
                self.categories.extend(subcategories)
            logger.info(f"Using {len(self.categories)} detailed categories")
        else:
            logger.info(f"Using {len(self.categories)} main categories")
    
    def _load_corrections(self):
        """Load user corrections from the stored file"""
        if os.path.exists(self.corrections_path):
            try:
                with open(self.corrections_path, 'r') as f:
                    self.corrections_data = json.load(f)
                logger.info(f"Loaded {len(self.corrections_data)} user corrections from {self.corrections_path}")
            except Exception as e:
                logger.warning(f"Could not load user corrections: {str(e)}")
                self.corrections_data = []
        else:
            self.corrections_data = []
    
    def preprocess_text(self, text):
        """
        Preprocess text for ML model with enhanced NLP processing
        
        Args:
            text (str): The text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        if not text or not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits (keeping $ for amount detection)
        text = re.sub(r'[^\w\s$]', ' ', text)
        
        # Extract named entities if SpaCy is available
        extracted_entities = []
        if self.nlp:
            try:
                doc = self.nlp(text)
                # Extract meaningful entity types: ORG, PRODUCT, GPE (locations), etc.
                meaningful_types = {'ORG', 'PRODUCT', 'GPE', 'PERSON', 'FAC', 'LOC'}
                extracted_entities = [ent.text.lower() for ent in doc.ents if ent.label_ in meaningful_types]
            except Exception as e:
                logger.debug(f"Error during NER: {str(e)}")
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Tokenize using SpaCy if available
        tokens = []
        if self.nlp:
            try:
                doc = self.nlp(text)
                tokens = [token.text for token in doc]
            except Exception as e:
                logger.debug(f"Error in SpaCy tokenization: {str(e)}")
                tokens = text.split()
        else:
            # Simple tokenization (split by spaces)
            tokens = text.split()
        
        # Remove stopwords and lemmatize
        try:
            processed_tokens = [
                self.lemmatizer.lemmatize(token) for token in tokens 
                if token not in self.stop_words and len(token) > 2
            ]
        except Exception as e:
            logger.warning(f"Error in lemmatization: {str(e)}")
            # Fallback: just remove stopwords without lemmatization
            processed_tokens = [
                token for token in tokens 
                if token not in self.stop_words and len(token) > 2
            ]
        
        # Add back named entities to ensure they're preserved
        if extracted_entities:
            processed_tokens.extend(extracted_entities)
        
        return " ".join(processed_tokens)
    
    def _extract_amount_features(self, amount):
        """
        Extract features from the amount to enhance categorization with more granular ranges
        
        Args:
            amount (float): Transaction amount
            
        Returns:
            dict: Features based on amount
        """
        features = {}
        
        if amount is None:
            return features
            
        # Convert to float if needed
        if isinstance(amount, str):
            try:
                amount = float(amount.replace('$', '').replace(',', ''))
            except:
                return features
        
        # More granular amount range features
        if amount < 5:
            features['very_small_amount'] = True
        elif amount < 15:
            features['small_amount'] = True
        elif amount < 30:
            features['coffee_meal_amount'] = True
        elif amount < 50:
            features['medium_amount'] = True
        elif amount < 100:
            features['large_amount'] = True
        elif amount < 200:
            features['xl_amount'] = True
        elif amount < 500:
            features['xxl_amount'] = True
        elif amount < 1000:
            features['major_purchase'] = True
        else:
            features['very_large_purchase'] = True
            
        # Day-to-day transaction or significant purchase
        if amount < 100:
            features['day_to_day_expense'] = True
        else:
            features['significant_expense'] = True
            
        # Exact amount features (common price points)
        if amount == int(amount):
            features['round_number_amount'] = True
            
        # Common subscription price points
        subscription_price_points = [9.99, 10.99, 12.99, 14.99, 15.99, 19.99]
        for price in subscription_price_points:
            if abs(amount - price) < 0.01:
                features['subscription_price_point'] = True
                break
            
        return features
    
    def train(self, descriptions, categories, amounts=None, grid_search=False):
        """
        Train the categorization model with enhanced features and XGBoost
        
        Args:
            descriptions (list): List of expense descriptions
            categories (list): List of corresponding categories
            amounts (list, optional): List of transaction amounts
            grid_search (bool): Whether to use grid search for hyperparameter tuning
            
        Returns:
            dict: Dictionary with model performance metrics
        """
        if len(descriptions) != len(categories):
            raise ValueError("Descriptions and categories must have the same length")
            
        if len(descriptions) == 0:
            raise ValueError("No training data provided")
            
        # Include amounts if provided
        has_amounts = amounts is not None and len(amounts) == len(descriptions)
        logger.info(f"Training with amount data: {has_amounts}")
        
        # Preprocess descriptions
        processed_descriptions = [self.preprocess_text(desc) for desc in descriptions]
        
        # Create DataFrame
        data = pd.DataFrame({
            'description': processed_descriptions,
            'category': categories
        })
        
        if has_amounts:
            data['amount'] = amounts
        
        # Remove empty descriptions
        data = data[data['description'].str.strip() != '']
        
        if len(data) == 0:
            raise ValueError("No valid training data after preprocessing")
            
        # Add user corrections to training data if available
        if self.corrections_data:
            for correction in self.corrections_data:
                if 'description' in correction and 'category' in correction:
                    processed_desc = self.preprocess_text(correction['description'])
                    if processed_desc:  # Only add if valid after preprocessing
                        new_row = {'description': processed_desc, 'category': correction['category']}
                        if 'amount' in correction and has_amounts:
                            new_row['amount'] = float(correction['amount'])
                        # Add to dataframe with index handling
                        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
            
            logger.info(f"Added {len(self.corrections_data)} user corrections to training data")
            
        # Print class distribution
        class_distribution = data['category'].value_counts()
        logger.info(f"Class distribution: {class_distribution}")
        
        # Encode categories as integers for XGBoost
        label_encoder = LabelEncoder()
        encoded_categories = label_encoder.fit_transform(data['category'])
        self.label_encoder = label_encoder  # Save for later use
        
        # Split features and labels
        X = data['description']
        y = encoded_categories  # Use encoded categories
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, 
            y, 
            test_size=0.2,
            random_state=42,
            stratify=y
        )
        
        # Initialize vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2)
        )
        
        # Fit vectorizer on training data
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Get features and calculate category keywords
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Use original categories for keywords (not encoded)
        # Fix for numpy.ndarray not having index attribute
        if hasattr(y_train, 'index'):
            y_train_original = data['category'].iloc[y_train.index]
        else:
            # For numpy arrays, we recreate the mapping based on the original indices before splitting
            train_indices = np.arange(len(X))[np.isin(np.arange(len(X)), np.arange(len(X_train)))]
            y_train_original = data['category'].iloc[train_indices].reset_index(drop=True)
        
        self._build_category_keywords(X_train_vec, y_train_original, feature_names)
        
        # Train appropriate model based on model_type
        if self.model_type == "xgboost":
            if grid_search:
                logger.info("Using grid search for XGBoost hyperparameter tuning")
                param_grid = {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'subsample': [0.8, 1.0],
                    'colsample_bytree': [0.8, 1.0]
                }
                
                self.model = GridSearchCV(
                    xgb.XGBClassifier(
                        objective='multi:softprob',
                        random_state=42
                    ),
                    param_grid,
                    cv=5,
                    n_jobs=-1,
                    verbose=1,
                    scoring='f1_weighted'
                )
                
                self.model.fit(X_train_vec, y_train)
                logger.info(f"Best parameters: {self.model.best_params_}")
                self.model = self.model.best_estimator_
            else:
                # Initialize and train model with sensible defaults
                self.model = xgb.XGBClassifier(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    objective='multi:softprob',
                    random_state=42
                )
                
                self.model.fit(X_train_vec, y_train)
        else:
            # Fallback to RandomForest if XGBoost not specified
            logger.info("Using RandomForest classifier as fallback")
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train_vec, y_train)
        
        # Create SHAP explainer (for XGBoost only)
        if self.model_type == "xgboost":
            try:
                # Only use a subset of training data for computational efficiency
                explainer_train = X_train_vec[:min(500, X_train_vec.shape[0])]
                self.shap_explainer = shap.TreeExplainer(self.model, explainer_train)
                logger.info("SHAP explainer created successfully")
            except Exception as e:
                logger.warning(f"Could not create SHAP explainer: {str(e)}")
                self.shap_explainer = None
        
        # Calculate metrics on test set (decoding the encoded categories first)
        y_pred = self.model.predict(X_test_vec)
        y_test_original = label_encoder.inverse_transform(y_test)
        y_pred_original = label_encoder.inverse_transform(y_pred)
        
        accuracy = accuracy_score(y_test_original, y_pred_original)
        precision = precision_score(y_test_original, y_pred_original, average='weighted')
        recall = recall_score(y_test_original, y_pred_original, average='weighted')
        f1 = f1_score(y_test_original, y_pred_original, average='weighted')
        
        # Log classifier report
        report = classification_report(y_test_original, y_pred_original)
        logger.info(f"Classification report:\n{report}")
        
        # Store feature importances
        self._store_feature_importances(feature_names)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'report': report
        }
    
    def _build_category_keywords(self, X_train_vec, y_train, feature_names):
        """
        Build a dictionary of keywords strongly associated with each category
        
        Args:
            X_train_vec: Vectorized training data
            y_train: Training labels
            feature_names: Feature names from vectorizer
        """
        self.category_keywords = {}
        
        # Convert sparse matrix to array for easier handling
        X_dense = X_train_vec.toarray()
        
        # For each category, find the most common terms
        for category in set(y_train):
            # Get indices of examples in this category
            category_indices = [i for i, cat in enumerate(y_train) if cat == category]
            
            if not category_indices:
                continue
                
            # Get feature vectors for this category
            category_vectors = X_dense[category_indices]
            
            # Sum up term frequencies for this category
            term_sums = np.sum(category_vectors, axis=0)
            
            # Sort terms by frequency
            sorted_indices = term_sums.argsort()[::-1]
            
            # Get top 20 terms
            top_terms = [(feature_names[i], term_sums[i]) for i in sorted_indices[:20] if term_sums[i] > 0]
            
            self.category_keywords[category] = top_terms
    
    def _store_feature_importances(self, feature_names):
        """
        Store feature importances by category
        
        Args:
            feature_names: List of feature names from vectorizer
        """
        # Get overall feature importances
        importances = self.model.feature_importances_
        
        # Sort features by importance
        indices = np.argsort(importances)[::-1]
        
        # Store top features for each category
        for idx, category in enumerate(self.model.classes_):
            self.feature_importances[category] = []
            
            # If using RandomForestClassifier, get feature importance for each class
            if hasattr(self.model, 'estimators_'):
                class_importances = []
                
                for tree in self.model.estimators_:
                    if hasattr(tree, 'tree_'):
                        # Extract the class-specific importance from each tree
                        for i, importance in enumerate(tree.feature_importances_):
                            if importance > 0:
                                class_importances.append((feature_names[i], importance))
                
                # Aggregate and sort
                if class_importances:
                    counter = Counter(name for name, _ in class_importances)
                    
                    # Get the features that appear most frequently
                    most_common = counter.most_common(20)
                    
                    # Create a list of tuples (feature, importance score)
                    self.feature_importances[category] = [
                        (feature, count/len(self.model.estimators_)) 
                        for feature, count in most_common
                    ]
    
    def predict_category(self, description, amount=None):
        """
        Predict the category for an expense description with enhanced confidence scoring
        
        Args:
            description (str): The expense description
            amount (float, optional): The amount of the expense
            
        Returns:
            tuple: (predicted_category, confidence, explanation)
        """
        # --- CORRECTION OVERRIDE LOGIC ---
        # Check for global/user correction in the database first
        db_correction = self._get_db_correction(description, amount)
        if db_correction is not None:
            return (
                db_correction.correct_category,
                1.0,
                "Correction applied (from database)"
            )
        # Check for user correction in memory/file (legacy fallback)
        if self.corrections_data:
            # Try to match both description and (if provided) amount
            for correction in reversed(self.corrections_data):  # use most recent if multiple
                if correction.get("description", "").strip().lower() == description.strip().lower():
                    # If amount is provided, match it if present in correction
                    if amount is not None and "amount" in correction:
                        try:
                            if abs(float(correction["amount"]) - float(amount)) < 0.01:
                                return (
                                    correction["category"],
                                    1.0,
                                    "User correction applied (matched description and amount)"
                                )
                        except Exception:
                            pass  # fallback to description-only match if amount parsing fails
                    elif amount is None or "amount" not in correction:
                        # If no amount provided or stored, match on description only
                        return (
                            correction["category"],
                            0.95,
                            "User correction applied (matched description)"
                        )
        # --- END CORRECTION OVERRIDE LOGIC ---

        if not self.model or not self.vectorizer:
            # Auto-train the model if it's not already trained
            logger.info("Model not trained. Auto-training now...")
            try:
                self.train_with_default_data()
            except Exception as e:
                logger.error(f"Auto-training failed: {e}")
                return ("Uncategorized", 0.0, "Model not trained")

        # Preprocess text
        processed_text = self.preprocess_text(description)
        
        if not processed_text:
            # Default to Miscellaneous if no usable text
            return "Miscellaneous", 0.0, "Insufficient description for prediction"
        
        # Convert to vector
        X = self.vectorizer.transform([processed_text])
        
        # Get probabilities for all categories
        probabilities = self.model.predict_proba(X)[0]
        
        # Get category with highest probability
        max_prob_index = np.argmax(probabilities)
        
        # Convert from encoded index to category name
        if hasattr(self, 'label_encoder'):
            predicted_category = self.label_encoder.inverse_transform([max_prob_index])[0]
        else:
            predicted_category = self.model.classes_[max_prob_index]
            
        confidence = probabilities[max_prob_index]
        
        # Get explanation using SHAP values if available
        explanation = self._get_prediction_explanation(X, processed_text, predicted_category)
        
        # If confidence is low, try to use amount and rules to improve prediction
        if confidence < 0.5 and amount is not None:
            # Apply some amount-based heuristics
            if amount > 1000:
                # Large amounts are often housing, investments, or education
                housing_idx = self._get_category_index("Housing")
                investment_idx = self._get_category_index("Investments")
                education_idx = self._get_category_index("Education")
                
                if housing_idx >= 0 and probabilities[housing_idx] > 0.1:
                    predicted_category = "Housing"
                    confidence = max(confidence, probabilities[housing_idx] * 1.2)
                    explanation += f" (amount-based adjustment: large amount suggests Housing category)"
                elif investment_idx >= 0 and probabilities[investment_idx] > 0.1:
                    predicted_category = "Investments"
                    confidence = max(confidence, probabilities[investment_idx] * 1.2)
                    explanation += f" (amount-based adjustment: large amount suggests Investment category)"
                elif education_idx >= 0 and probabilities[education_idx] > 0.1:
                    predicted_category = "Education"
                    confidence = max(confidence, probabilities[education_idx] * 1.2)
                    explanation += f" (amount-based adjustment: large amount suggests Education category)"
            elif amount < 15:
                # Small amounts often food, transportation, or miscellaneous
                food_idx = self._get_category_index("Food & Dining")
                transport_idx = self._get_category_index("Transportation")
                
                if food_idx >= 0 and probabilities[food_idx] > 0.1:
                    predicted_category = "Food & Dining"
                    confidence = max(confidence, probabilities[food_idx] * 1.2)
                    explanation += f" (amount-based adjustment: small amount suggests Food & Dining category)"
                elif transport_idx >= 0 and probabilities[transport_idx] > 0.1:
                    predicted_category = "Transportation"
                    confidence = max(confidence, probabilities[transport_idx] * 1.2)
                    explanation += f" (amount-based adjustment: small amount suggests Transportation category)"
        
        # Handle common subscription price points
        subscription_price_points = [9.99, 10.99, 12.99, 14.99, 15.99, 19.99]
        entertainment_idx = self._get_category_index("Entertainment")
        utilities_idx = self._get_category_index("Utilities")
        
        if any(abs(amount - price) < 0.01 for price in subscription_price_points):
            if entertainment_idx >= 0 and probabilities[entertainment_idx] > 0.05:
                if confidence < 0.6:  # Only override if we're not very confident
                    predicted_category = "Entertainment"
                    confidence = max(confidence, 0.6)
                    explanation += f" (rule-based: subscription price point suggests Entertainment category)"
            elif utilities_idx >= 0 and probabilities[utilities_idx] > 0.05:
                if confidence < 0.6:  # Only override if we're not very confident
                        predicted_category = "Utilities"
                        confidence = max(confidence, 0.6)
                        explanation += f" (rule-based: subscription price point suggests Utilities category)"
        
        # Look for keywords in low-confidence predictions
        if confidence < 0.4:
            health_keywords = {'doctor', 'dentist', 'hospital', 'medical', 'health', 'prescription', 'pharmacy'}
            food_keywords = {'restaurant', 'grocery', 'cafe', 'coffee', 'food', 'meal', 'takeout', 'lunch', 'dinner'}
            transport_keywords = {'gas', 'bus', 'train', 'taxi', 'uber', 'lyft', 'fare', 'metro', 'subway'}
            
            words = set(processed_text.split())
            
            health_idx = self._get_category_index("Healthcare")
            food_idx = self._get_category_index("Food & Dining")
            transport_idx = self._get_category_index("Transportation")
            
            if health_idx >= 0 and any(keyword in words for keyword in health_keywords):
                predicted_category = "Healthcare"
                confidence = max(confidence, 0.7)
                explanation += f" (keyword match: medical terms suggest Healthcare category)"
            elif food_idx >= 0 and any(keyword in words for keyword in food_keywords):
                predicted_category = "Food & Dining"
                confidence = max(confidence, 0.7)
                explanation += f" (keyword match: food terms suggest Food & Dining category)"
            elif transport_idx >= 0 and any(keyword in words for keyword in transport_keywords):
                predicted_category = "Transportation"
                confidence = max(confidence, 0.7)
                explanation += f" (keyword match: transport terms suggest Transportation category)"
        
        return predicted_category, confidence, explanation
    
    def _get_prediction_explanation(self, X_vec, processed_text, predicted_category):
        """
        Get an explanation for a prediction using SHAP values or keywords
        
        Args:
            X_vec: Vectorized input
            processed_text: Preprocessed text
            predicted_category: The predicted category
            
        Returns:
            str: Human-readable explanation
        """
        explanation = f"Predicted as {predicted_category}"
        
        # Try to use SHAP values for explanation
        if self.shap_explainer is not None:
            try:
                # Get SHAP values
                shap_values = self.shap_explainer.shap_values(X_vec)
                
                # Get category index
                category_idx = list(self.model.classes_).index(predicted_category)
                
                # Get feature names
                feature_names = self.vectorizer.get_feature_names_out()
                
                # Get the non-zero features in this sample
                x_dense = X_vec.toarray()[0]
                feature_indexes = np.where(x_dense > 0)[0]
                
                # For these features, get their SHAP values for this class
                feature_shap_values = [(feature_names[i], shap_values[category_idx][0, i]) 
                                       for i in feature_indexes]
                
                # Sort by absolute SHAP value
                feature_shap_values.sort(key=lambda x: abs(x[1]), reverse=True)
                
                # Get top contributing features
                top_features = feature_shap_values[:3]
                
                if top_features:
                    explanation += ". Key factors: "
                    for feature, value in top_features:
                        impact = "positively" if value > 0 else "negatively"
                        explanation += f"{feature} ({impact}), "
                    explanation = explanation.rstrip(", ")
            except Exception as e:
                logger.debug(f"Error getting SHAP explanation: {str(e)}")
                # Fall back to keyword-based explanation
                explanation += self._get_keyword_explanation(processed_text, predicted_category)
        else:
            # Fall back to keyword-based explanation
            explanation += self._get_keyword_explanation(processed_text, predicted_category)
            
        return explanation
    
    def _get_keyword_explanation(self, processed_text, category):
        """Get explanation based on keywords"""
        explanation = ""
        
        if category in self.category_keywords:
            words = set(processed_text.split())
            matches = []
            
            # Look for matches between important category keywords and input text
            for keyword, _ in self.category_keywords[category][:10]:
                if keyword in words:
                    matches.append(keyword)
            
            if matches:
                explanation += f". Matched keywords: {', '.join(matches)}"
            else:
                explanation += f". Similar to other {category} transactions"
        
        return explanation
    
    def add_user_correction(self, description, correct_category, amount=None):
        """
        Add a user correction to improve future predictions
        
        Args:
            description (str): The expense description
            correct_category (str): The correct category
            amount (float, optional): The amount of the expense
            
        Returns:
            bool: Whether the correction was successfully added
        """
        try:
            # Validate the category
            if (not self.use_detailed_categories and correct_category not in CATEGORY_HIERARCHY) or \
               (self.use_detailed_categories and not any(correct_category in subcats for subcats in CATEGORY_HIERARCHY.values())):
                logger.warning(f"Invalid category in user correction: {correct_category}")
                return False
            
            # Create correction entry
            correction = {
                "description": description,
                "category": correct_category,
                "timestamp": datetime.now().isoformat()
            }
            
            if amount is not None:
                correction["amount"] = float(amount)
            
            # Add to corrections data
            self.corrections_data.append(correction)
            
            # Save corrections to file
            self._save_corrections()
            
            logger.info(f"Added user correction: {description} → {correct_category}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user correction: {str(e)}")
            return False
    
    def _save_corrections(self):
        """Save user corrections to the stored file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.corrections_path), exist_ok=True)
            
            with open(self.corrections_path, 'w') as f:
                json.dump(self.corrections_data, f, indent=2)
                
            logger.info(f"Saved {len(self.corrections_data)} user corrections to {self.corrections_path}")
            return True
        except Exception as e:
            logger.error(f"Could not save user corrections: {str(e)}")
            return False
    
    def retrain_with_corrections(self):
        """
        Retrain the model incorporating user corrections
        
        Returns:
            dict: Dictionary with model performance metrics, or None if failed
        """
        try:
            # Load existing corrections
            self._load_corrections()
            
            if not self.corrections_data:
                logger.info("No user corrections available for retraining")
                return None
            
            logger.info(f"Retraining with {len(self.corrections_data)} user corrections")
            
            # Train with default data, which will incorporate corrections
            return self.train_with_default_data()
        except Exception as e:
            logger.error(f"Error retraining with corrections: {str(e)}")
            return None
    
    def _get_category_index(self, category_name):
        """Get the index of a category in the model classes"""
        try:
            if hasattr(self, 'label_encoder'):
                # Convert category name to encoded value
                encoded_category = self.label_encoder.transform([category_name])[0]
                # Return the index of this encoded value
                return int(encoded_category)
            else:
                return list(self.model.classes_).index(category_name)
        except (ValueError, KeyError) as e:
            logger.debug(f"Category not found in model classes: {category_name}, error: {str(e)}")
            return -1
    
    def convert_to_main_category(self, subcategory):
        """
        Convert a subcategory to its main category
        
        Args:
            subcategory (str): The subcategory name
            
        Returns:
            str: The main category name, or the original value if not found
        """
        for main_category, subcategories in CATEGORY_HIERARCHY.items():
            if subcategory in subcategories:
                return main_category
        return subcategory  # Return original if not found
    
    def get_subcategories(self, main_category):
        """
        Get subcategories for a main category
        
        Args:
            main_category (str): Main category name
            
        Returns:
            list: List of subcategories
        """
        return CATEGORY_HIERARCHY.get(main_category, [])
    
    def get_top_features(self, category, n=10):
        """
        Get the top features (keywords) for a category
        
        Args:
            category (str): The category name
            n (int): Number of features to return
            
        Returns:
            list: List of (feature, importance) tuples
        """
        if category in self.feature_importances:
            return self.feature_importances[category][:n]
        elif category in self.category_keywords:
            return self.category_keywords[category][:n]
        else:
            return []
    
    def train_with_default_data(self, use_detailed=None):
        """
        Train the model with default example data
        
        Args:
            use_detailed (bool, optional): Override the use_detailed_categories setting
            
        Returns:
            float: Model accuracy
        """
        use_detailed = use_detailed if use_detailed is not None else self.use_detailed_categories
        
        if use_detailed:
            # Import the training data generator function
            from .training_data import generate_detailed_training_data
            
            # Generate detailed training data
            training_data = generate_detailed_training_data()
            logger.info(f"Training with {len(training_data['descriptions'])} detailed examples")
            
            return self.train(
                training_data['descriptions'],
                training_data['categories']
            )
        else:
            # Import the main category training data
            from .training_data import MAIN_CATEGORY_TRAINING_DATA
            
            logger.info(f"Training with {len(MAIN_CATEGORY_TRAINING_DATA['descriptions'])} main category examples")
            
            return self.train(
                MAIN_CATEGORY_TRAINING_DATA['descriptions'],
                MAIN_CATEGORY_TRAINING_DATA['categories']
            )