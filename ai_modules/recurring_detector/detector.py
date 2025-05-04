"""
Recurring Transaction Detector Module

This module analyzes financial transaction data to identify recurring payments and subscription patterns.
It uses time-series analysis and pattern recognition to detect regular payments that likely represent
subscriptions or recurring bills.

Features:
- Identifies transactions that occur at regular intervals
- Calculates monthly and annual costs of recurring transactions
- Predicts upcoming payment dates
- Categorizes recurring payments (subscriptions, bills, etc.)
- Identifies potential savings opportunities
"""

import re
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecurringTransactionDetector:
    """
    A class for detecting recurring transactions and subscription patterns in financial data.
    
    The detector analyzes transaction history to identify regular payments that occur at
    consistent intervals (monthly, weekly, yearly, etc.) with similar amounts.
    """
    
    def __init__(self, min_occurrences=3, time_window_days=365, amount_variance=0.05, date_variance_days=2):
        """
        Initialize the detector with configuration parameters.
        
        Args:
            min_occurrences (int): Minimum number of occurrences to identify a pattern
            time_window_days (int): Number of days to look back for analysis
            amount_variance (float): Allowed variance in transaction amounts (0.05 = 5%)
            date_variance_days (int): Allowed variance in days for periodic transactions
        """
        self.min_occurrences = min_occurrences
        self.time_window_days = time_window_days
        self.amount_variance = amount_variance
        self.date_variance_days = date_variance_days
        self.patterns = []
        self.df = None
        self.stats = {
            'monthly_subscription_cost': 0,
            'annual_subscription_cost': 0,
            'total_subscriptions': 0,
            'upcoming_payments': []
        }
        
        # Subscription keywords to help identify subscription services
        self.subscription_keywords = [
            'netflix', 'spotify', 'hulu', 'amazon prime', 'disney+', 'apple tv', 
            'apple music', 'youtube premium', 'hbo', 'subscription', 'member', 
            'monthly', 'recurring', 'audible', 'prime video', 'prime membership',
            'paramount+', 'peacock', 'tidal', 'deezer', 'xbox', 'playstation',
            'adobe', 'google one', 'icloud', 'github', 'dropbox', 'onedrive',
            'gym', 'fitness', 'monthly fee', 'annual fee', 'magazine'
        ]
    
    def _is_likely_subscription(self, description):
        """
        Check if a transaction description contains keywords suggesting it's a subscription.
        
        Args:
            description (str): Transaction description
            
        Returns:
            bool: True if likely a subscription, False otherwise
        """
        description = description.lower()
        return any(keyword in description for keyword in self.subscription_keywords)
    
    def _preprocess_data(self, transactions):
        """
        Preprocess transaction data into a pandas DataFrame for analysis.
        
        Args:
            transactions (list): List of transaction dictionaries
            
        Returns:
            pandas.DataFrame: Preprocessed transaction data
        """
        if not transactions:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Ensure date is datetime type
        if 'date' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])
        else:
            logger.error("Transaction data missing 'date' column")
            return pd.DataFrame()
            
        # Filter to transactions within time window
        cutoff_date = datetime.now() - timedelta(days=self.time_window_days)
        df = df[df['date'] >= cutoff_date]
        
        # Sort by date
        df = df.sort_values('date')
        
        # Add is_subscription flag based on description
        df['is_subscription'] = df['description'].apply(self._is_likely_subscription)
        
        self.df = df
        return df
    
    def _find_similar_transactions(self):
        """
        Group similar transactions by description and amount similarity.
        
        Returns:
            dict: Groups of similar transactions
        """
        if self.df is None or self.df.empty:
            return {}
        
        # Group by exact description first
        description_groups = self.df.groupby('description')
        
        similar_groups = {}
        for desc, group in description_groups:
            # If we already have enough transactions with exact same description
            if len(group) >= self.min_occurrences:
                # Check if amounts are similar
                amounts = group['amount'].values
                mean_amount = np.mean(amounts)
                
                # If all amounts are within variance threshold
                if all(abs(amt - mean_amount) / mean_amount <= self.amount_variance for amt in amounts):
                    similar_groups[desc] = group
            
        # For transactions that don't yet form a pattern, try fuzzy matching descriptions
        # This helps catch variations like "NETFLIX US" and "NETFLIX" as the same service
        remaining = self.df[~self.df['description'].isin(similar_groups.keys())]
        
        # Create simplified descriptions for fuzzy matching
        remaining['simple_desc'] = remaining['description'].apply(
            lambda x: re.sub(r'[^a-zA-Z0-9]', '', x.lower())
        )
        
        for _, row in remaining.iterrows():
            simple_desc = row['simple_desc']
            orig_desc = row['description']
            amount = row['amount']
            
            # Skip if already in a group
            if orig_desc in similar_groups:
                continue
                
            # Find potential matches based on simplified description
            for key in list(similar_groups.keys()):
                simple_key = re.sub(r'[^a-zA-Z0-9]', '', key.lower())
                
                # Check if simplified descriptions are similar
                if (simple_key in simple_desc or simple_desc in simple_key) and len(simple_key) > 5:
                    # Check if amount is similar to the group's mean
                    group_mean = similar_groups[key]['amount'].mean()
                    if abs(amount - group_mean) / group_mean <= self.amount_variance:
                        # Add to existing group
                        similar_groups[key] = pd.concat([similar_groups[key], pd.DataFrame([row])])
                        break
        
        return similar_groups
    
    def _detect_intervals(self, group):
        """
        Detect time intervals between transactions in a group.
        
        Args:
            group (pandas.DataFrame): Group of similar transactions
            
        Returns:
            tuple: (interval_type, interval_days, confidence)
        """
        if len(group) < self.min_occurrences:
            return None, 0, 0
            
        # Sort by date
        group = group.sort_values('date')
        
        # Calculate days between consecutive transactions
        dates = group['date'].values
        intervals = []
        
        for i in range(1, len(dates)):
            delta = (dates[i] - dates[i-1]).days
            intervals.append(delta)
        
        if not intervals:
            return None, 0, 0
            
        # Check for consistent intervals
        intervals = np.array(intervals)
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # Determine interval type
        interval_type = None
        confidence = 0
        
        if std_interval / mean_interval <= 0.25:  # Fairly consistent interval
            if 25 <= mean_interval <= 35:
                interval_type = 'MONTHLY'
                confidence = 0.9
            elif 6 <= mean_interval <= 8:
                interval_type = 'WEEKLY'
                confidence = 0.9
            elif 13 <= mean_interval <= 16:
                interval_type = 'BIWEEKLY'
                confidence = 0.8
            elif 89 <= mean_interval <= 94:
                interval_type = 'QUARTERLY'
                confidence = 0.8
            elif 179 <= mean_interval <= 187:
                interval_type = 'SEMIANNUAL'
                confidence = 0.7
            elif 350 <= mean_interval <= 380:
                interval_type = 'ANNUAL'
                confidence = 0.7
            else:
                interval_type = f'EVERY_{round(mean_interval)}_DAYS'
                confidence = 0.6
                
        return interval_type, mean_interval, confidence
    
    def _predict_next_payment(self, group, interval_days):
        """
        Predict the next payment date based on observed pattern.
        
        Args:
            group (pandas.DataFrame): Group of similar transactions
            interval_days (float): Detected interval in days
            
        Returns:
            datetime: Predicted next payment date
        """
        if group.empty or interval_days <= 0:
            return None
            
        # Get the most recent transaction date
        last_date = group['date'].max()
        
        # Predict next date
        next_date = last_date + timedelta(days=round(interval_days))
        
        return next_date
    
    def detect_recurring_transactions(self, transactions):
        """
        Analyze transactions to identify recurring payment patterns.
        
        Args:
            transactions (list): List of transaction dictionaries with date, description, and amount
            
        Returns:
            list: Detected recurring transaction patterns
        """
        # Reset patterns and stats
        self.patterns = []
        self.stats = {
            'monthly_subscription_cost': 0,
            'annual_subscription_cost': 0,
            'total_subscriptions': 0,
            'upcoming_payments': []
        }
        
        # Preprocess data
        df = self._preprocess_data(transactions)
        if df.empty:
            logger.warning("No transactions to analyze or preprocessing failed")
            return []
            
        # Find similar transaction groups
        similar_groups = self._find_similar_transactions()
        
        # Analyze each group for recurring patterns
        monthly_total = 0
        annual_total = 0
        
        for desc, group in similar_groups.items():
            if len(group) < self.min_occurrences:
                continue
                
            # Detect time intervals
            interval_type, interval_days, confidence = self._detect_intervals(group)
            
            if interval_type:
                # Calculate average amount
                avg_amount = group['amount'].mean()
                
                # Predict next payment
                next_date = self._predict_next_payment(group, interval_days)
                
                # Determine if it's likely a subscription
                is_subscription = group['is_subscription'].any()
                
                # Calculate monthly and annual cost
                monthly_cost = 0
                annual_cost = 0
                
                if interval_type == 'WEEKLY':
                    monthly_cost = avg_amount * 4.33  # Average weeks per month
                    annual_cost = avg_amount * 52
                elif interval_type == 'BIWEEKLY':
                    monthly_cost = avg_amount * 2.17  # Average biweekly periods per month
                    annual_cost = avg_amount * 26
                elif interval_type == 'MONTHLY':
                    monthly_cost = avg_amount
                    annual_cost = avg_amount * 12
                elif interval_type == 'QUARTERLY':
                    monthly_cost = avg_amount / 3
                    annual_cost = avg_amount * 4
                elif interval_type == 'SEMIANNUAL':
                    monthly_cost = avg_amount / 6
                    annual_cost = avg_amount * 2
                elif interval_type == 'ANNUAL':
                    monthly_cost = avg_amount / 12
                    annual_cost = avg_amount
                elif interval_type.startswith('EVERY_'):
                    days = int(interval_type.split('_')[1])
                    monthly_cost = avg_amount * (30 / days)
                    annual_cost = avg_amount * (365 / days)
                
                # Add to totals if it's a subscription
                if is_subscription:
                    monthly_total += monthly_cost
                    annual_total += annual_cost
                
                # Create pattern object
                pattern = {
                    'description': desc,
                    'avg_amount': round(avg_amount, 2),
                    'interval_type': interval_type,
                    'interval_days': round(interval_days),
                    'confidence': round(confidence, 2),
                    'occurrences': len(group),
                    'is_subscription': is_subscription,
                    'transactions': group.to_dict('records'),
                    'monthly_cost': round(monthly_cost, 2),
                    'annual_cost': round(annual_cost, 2),
                    'next_date': next_date.strftime('%Y-%m-%d') if next_date else None
                }
                
                self.patterns.append(pattern)
                
                # If next payment is within 7 days, add to upcoming payments
                if next_date and (next_date - datetime.now()).days <= 7:
                    self.stats['upcoming_payments'].append({
                        'description': desc,
                        'amount': round(avg_amount, 2),
                        'date': next_date.strftime('%Y-%m-%d')
                    })
        
        # Sort patterns by annual cost (descending)
        self.patterns.sort(key=lambda x: x['annual_cost'], reverse=True)
        
        # Update stats
        self.stats['monthly_subscription_cost'] = round(monthly_total, 2)
        self.stats['annual_subscription_cost'] = round(annual_total, 2)
        self.stats['total_subscriptions'] = sum(1 for p in self.patterns if p['is_subscription'])
        
        return self.patterns
    
    def get_stats(self):
        """
        Get statistics about detected recurring transactions.
        
        Returns:
            dict: Statistics including monthly and annual costs
        """
        return self.stats
    
    def predict_annual_costs(self):
        """
        Predict annual costs for each recurring transaction.
        
        Returns:
            list: Sorted list of transactions with predicted annual costs
        """
        annual_costs = []
        
        for pattern in self.patterns:
            annual_costs.append({
                'description': pattern['description'],
                'annual_cost': pattern['annual_cost'],
                'monthly_cost': pattern['monthly_cost'],
                'is_subscription': pattern['is_subscription']
            })
            
        # Sort by annual cost (highest first)
        annual_costs.sort(key=lambda x: x['annual_cost'], reverse=True)
        
        return annual_costs 