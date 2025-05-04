"""
ExpenseClassifier

A machine learning model for expense categorization with support for retraining based on user corrections.
This model uses NLP techniques and scikit-learn for classification.
"""

import re
import numpy as np
import pandas as pd
import os
import json
import pickle
import logging
from datetime import datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.preprocessing import LabelEncoder
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Standard finance expense categories
EXPENSE_CATEGORIES = [
    'Food & Dining', 
    'Transportation',
    'Housing',
    'Utilities',
    'Healthcare',
    'Entertainment',
    'Shopping',
    'Personal Care',
    'Education',
    'Travel',
    'Gifts & Donations',
    'Insurance',
    'Taxes',
    'Business Services',
    'Investments',
    'Miscellaneous'
]

class TextPreprocessor:
    """Handles text preprocessing for NLP models"""
    
    def __init__(self):
        """Initialize the preprocessor with NLP components"""
        # Ensure NLTK resources are downloaded
        self._download_nltk_resources()
        
        # Setup NLP components
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
    
    def _download_nltk_resources(self):
        """Download required NLTK resources"""
        try:
            # Set custom path for NLTK data
            nltk_data_dir = str(Path.home() / 'nltk_data')
            os.makedirs(nltk_data_dir, exist_ok=True)
            nltk.data.path.append(nltk_data_dir)
            
            # Download required resources
            for resource in ['stopwords', 'wordnet', 'punkt']:
                try:
                    nltk.data.find(f'corpora/{resource}' if resource != 'punkt' else f'tokenizers/{resource}')
                    logger.debug(f"NLTK resource '{resource}' already available")
                except LookupError:
                    logger.info(f"Downloading NLTK resource: {resource}")
                    nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
        
        except Exception as e:
            logger.warning(f"Failed to download NLTK resources: {str(e)}")
            logger.warning("Some text preprocessing features may be limited")
    
    def preprocess(self, text):
        """
        Preprocess text for machine learning
        
        Args:
            text (str): Raw text
            
        Returns:
            str: Processed text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters (keep letters, numbers, spaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Tokenize
        tokens = text.split()
        
        # Remove stopwords and lemmatize tokens
        processed_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        # Rejoin into a string
        return " ".join(processed_tokens)


class ExpenseClassifier:
    """Expense categorization model with retraining support"""
    
    def __init__(self, model_dir="models"):
        """Initialize the classifier with default settings"""
        # Setup components
        self.preprocessor = TextPreprocessor()
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            min_df=2,
            ngram_range=(1, 2)
        )
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            min_samples_split=2,
            random_state=42
        )
        self.label_encoder = LabelEncoder()
        
        # For tracking
        self.is_trained = False
        self.model_version = 1
        self.last_trained = None
        self.accuracy = None
        self.feature_importances = {}
        
        # Storage paths
        self.model_dir = model_dir
        self.ensure_model_dir()
        
        # Default supported categories
        self.categories = EXPENSE_CATEGORIES
        self.label_encoder.fit(self.categories)
    
    def ensure_model_dir(self):
        """Ensure model directory exists"""
        os.makedirs(self.model_dir, exist_ok=True)
        
    def _get_model_path(self):
        """Get path for saving the model"""
        return os.path.join(self.model_dir, f"expense_classifier_v{self.model_version}.pkl")
    
    def _get_vectorizer_path(self):
        """Get path for saving the vectorizer"""
        return os.path.join(self.model_dir, f"vectorizer_v{self.model_version}.pkl")
    
    def _get_metadata_path(self):
        """Get path for saving metadata"""
        return os.path.join(self.model_dir, f"metadata_v{self.model_version}.json")
    
    def save(self):
        """Save the model and all components"""
        try:
            # Save model
            with open(self._get_model_path(), 'wb') as f:
                pickle.dump(self.model, f)
            
            # Save vectorizer
            with open(self._get_vectorizer_path(), 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            # Save metadata
            metadata = {
                'version': self.model_version,
                'is_trained': self.is_trained,
                'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                'accuracy': self.accuracy,
                'categories': self.categories,
                'feature_importances': {
                    category: [(feature, float(importance)) for feature, importance in importances]
                    for category, importances in self.feature_importances.items()
                }
            }
            
            with open(self._get_metadata_path(), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Model version {self.model_version} saved successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False
    
    def load(self, version=None):
        """
        Load a saved model
        
        Args:
            version (int, optional): Version to load, or latest if None
            
        Returns:
            bool: Success flag
        """
        try:
            # Determine version to load
            if version is None:
                # Find latest version
                versions = []
                for filename in os.listdir(self.model_dir):
                    if filename.startswith("metadata_v") and filename.endswith(".json"):
                        try:
                            v = int(filename.split("_v")[1].split(".json")[0])
                            versions.append(v)
                        except:
                            pass
                
                if not versions:
                    logger.warning("No saved models found")
                    return False
                
                version = max(versions)
            
            # Set paths
            model_path = os.path.join(self.model_dir, f"expense_classifier_v{version}.pkl")
            vectorizer_path = os.path.join(self.model_dir, f"vectorizer_v{version}.pkl")
            metadata_path = os.path.join(self.model_dir, f"metadata_v{version}.json")
            
            # Check if files exist
            if not all(os.path.exists(p) for p in [model_path, vectorizer_path, metadata_path]):
                logger.error(f"Model version {version} files not found")
                return False
            
            # Load model
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load vectorizer
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Set properties
            self.model_version = metadata['version']
            self.is_trained = metadata['is_trained']
            self.last_trained = datetime.fromisoformat(metadata['last_trained']) if metadata['last_trained'] else None
            self.accuracy = metadata['accuracy']
            self.categories = metadata['categories']
            
            # Feature importances (converting from JSON-safe format)
            self.feature_importances = {
                category: [(feature, importance) for feature, importance in importances]
                for category, importances in metadata.get('feature_importances', {}).items()
            }
            
            # Update label encoder
            self.label_encoder.fit(self.categories)
            
            logger.info(f"Successfully loaded model version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
    
    def train(self, descriptions, categories, test_size=0.2):
        """
        Train the model on expense descriptions
        
        Args:
            descriptions (list): List of expense descriptions
            categories (list): List of categories
            test_size (float): Test size ratio (0.0-1.0)
            
        Returns:
            dict: Training results with metrics
        """
        if len(descriptions) != len(categories):
            raise ValueError("Descriptions and categories must have the same length")
        
        if len(descriptions) < 10:
            raise ValueError("Not enough training data (minimum 10 samples required)")
        
        # Preprocess descriptions
        if not hasattr(self, 'preprocessor') or self.preprocessor is None:
            self.preprocessor = TextPreprocessor()
            
        processed_descriptions = [self.preprocessor.preprocess(desc) for desc in descriptions]
        
        # Fit label encoder
        unique_categories = sorted(list(set(categories)))
        self.categories = unique_categories
        self.label_encoder.fit(unique_categories)
        encoded_categories = self.label_encoder.transform(categories)
        
        # Create vectors
        X = self.vectorizer.fit_transform(processed_descriptions)
        y = encoded_categories
        
        # Adjust test_size to ensure it's large enough for stratification
        # The test set must have at least one sample per class
        num_classes = len(unique_categories)
        min_test_size = num_classes / len(descriptions)
        adjusted_test_size = max(test_size, min_test_size)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=adjusted_test_size, random_state=42, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Store feature importances
        self._extract_feature_importances()
        
        # Update metadata
        self.is_trained = True
        self.last_trained = datetime.now()
        self.accuracy = accuracy
        self.model_version += 1
        
        # Save the new model
        self.save()
        
        # Return results
        results = {
            'accuracy': accuracy,
            'f1_score': f1,
            'train_samples': X_train.shape[0],
            'test_samples': X_test.shape[0],
            'classes': len(self.categories),
            'version': self.model_version - 1  # Current version after saving
        }
        
        return results
    
    def predict(self, description):
        """
        Predict category for an expense description
        
        Args:
            description (str): Expense description text
            
        Returns:
            dict: Prediction results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Preprocess
        processed_text = self.preprocessor.preprocess(description)
        
        # Vectorize
        X = self.vectorizer.transform([processed_text])
        
        # Predict
        encoded_category = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Get predicted category
        category = self.label_encoder.inverse_transform([encoded_category])[0]
        
        # Get confidence (probability of the predicted class)
        confidence = probabilities[encoded_category]
        
        # Get alternative predictions
        sorted_indices = np.argsort(probabilities)[::-1]
        alternatives = []
        
        for idx in sorted_indices[1:4]:  # Top 3 alternatives
            alt_category = self.label_encoder.inverse_transform([idx])[0]
            alt_confidence = probabilities[idx]
            
            alternatives.append({
                'category': alt_category,
                'confidence': float(alt_confidence)
            })
        
        # Create explanation
        explanation = self._generate_explanation(processed_text, category)
        
        return {
            'category': category,
            'confidence': float(confidence),
            'alternatives': alternatives,
            'explanation': explanation
        }
    
    def _extract_feature_importances(self):
        """Extract and store feature importances per category"""
        if not self.is_trained:
            return
        
        try:
            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get global feature importances
            importances = self.model.feature_importances_
            
            # Get indices for each category
            self.feature_importances = {}
            
            for category_idx, category in enumerate(self.label_encoder.classes_):
                # Create list of (feature, importance) tuples
                category_importance = []
                
                # For Random Forest, extract feature importances
                tree_feature_importances = []
                for tree in self.model.estimators_:
                    # Filter samples where this tree predicted the current category
                    if tree.classes_[tree.predict([0])[0]] == category_idx:
                        tree_feature_importances.append(tree.feature_importances_)
                
                # If we have importances for this category
                if tree_feature_importances:
                    avg_importances = np.mean(tree_feature_importances, axis=0)
                    
                    for idx, importance in enumerate(avg_importances):
                        if importance > 0:
                            category_importance.append((feature_names[idx], importance))
                    
                    # Sort by importance (descending)
                    category_importance.sort(key=lambda x: x[1], reverse=True)
                    
                    # Keep top 20 features
                    self.feature_importances[category] = category_importance[:20]
            
        except Exception as e:
            logger.warning(f"Failed to extract feature importances: {str(e)}")
    
    def _generate_explanation(self, processed_text, category):
        """
        Generate an explanation for a prediction
        
        Args:
            processed_text (str): Preprocessed description
            category (str): Predicted category
            
        Returns:
            str: Human-readable explanation
        """
        # Get tokens from processed text
        tokens = processed_text.split()
        
        # If no feature importances or tokens, return generic message
        if category not in self.feature_importances or not tokens:
            return f"This expense was classified as '{category}' based on its description."
        
        # Get important features for this category
        important_features = [feature for feature, _ in self.feature_importances[category]]
        
        # Find matching features in the description
        matching_features = []
        for token in tokens:
            if token in important_features:
                matching_features.append(token)
            else:
                # Check for bi-gram features
                for feature in important_features:
                    if ' ' in feature and token in feature.split():
                        for i in range(len(tokens) - 1):
                            if tokens[i] + ' ' + tokens[i+1] == feature:
                                matching_features.append(feature)
        
        # Remove duplicates
        matching_features = list(set(matching_features))
        
        if matching_features:
            if len(matching_features) == 1:
                return f"Classified as '{category}' because the description contains '{matching_features[0]}'."
            elif len(matching_features) == 2:
                return f"Classified as '{category}' because the description contains '{matching_features[0]}' and '{matching_features[1]}'."
            else:
                features_str = ', '.join([f"'{f}'" for f in matching_features[:-1]]) + f" and '{matching_features[-1]}'"
                return f"Classified as '{category}' because the description contains {features_str}."
        else:
            return f"This expense was classified as '{category}' based on its description."

    def add_training_data(self, new_data):
        """
        Add new training data and retrain the model
        
        Args:
            new_data (list): List of dict with keys 'description' and 'category'
            
        Returns:
            dict: Training results
        """
        if not new_data:
            return None
        
        # Load existing data if model is trained
        if self.is_trained:
            # Get feature names and sample data to recreate training dataset
            feature_names = self.vectorizer.get_feature_names_out()
            X_sample = self.vectorizer.transform(["sample text"])
            
            # We can't directly access the training data, so we'll generate synthetic data
            # This is a compromise, but sufficient for demonstration
            synthetic_descriptions = []
            synthetic_categories = []
            
            # Generate synthetic examples based on feature importances
            for category in self.feature_importances:
                # Get top features for this category
                top_features = [feature for feature, _ in self.feature_importances[category][:10]]
                
                # Create 3 synthetic examples per category
                for i in range(3):
                    # Use random 2-3 top features for this category
                    num_features = min(len(top_features), np.random.randint(2, 4))
                    features = np.random.choice(top_features, num_features, replace=False)
                    
                    # Create a synthetic description
                    synthetic_desc = " ".join(features)
                    synthetic_descriptions.append(synthetic_desc)
                    synthetic_categories.append(category)
        else:
            # If not trained, start with empty lists
            synthetic_descriptions = []
            synthetic_categories = []
        
        # Add new data
        for item in new_data:
            if 'description' in item and 'category' in item:
                synthetic_descriptions.append(item['description'])
                synthetic_categories.append(item['category'])
        
        # Train with combined data
        results = self.train(synthetic_descriptions, synthetic_categories)
        
        return results 