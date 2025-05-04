import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExpenseInsights:
    """
    Analyzes expense data to generate personalized financial insights and recommendations
    Uses basic statistics and pattern recognition to identify trends in spending
    """
    
    def __init__(self):
        """Initialize the insights engine"""
        self.insight_types = {
            'spending_pattern': self._analyze_spending_patterns,
            'category_analysis': self._analyze_categories,
            'unusual_transactions': self._find_unusual_transactions,
            'saving_opportunities': self._find_saving_opportunities,
            'recurring_expenses': self._find_recurring_expenses
        }
    
    def generate_insights(self, expenses, user_data=None, types=None):
        """
        Generate insights from expense data
        
        Args:
            expenses: List of expense objects with amount, category, date
            user_data: Optional user information for personalization
            types: Types of insights to generate (None = all)
            
        Returns:
            Dictionary of insights by type
        """
        if not expenses:
            return {'error': 'No expense data provided'}
            
        # Convert expenses to DataFrame for easier analysis
        try:
            df = self._prepare_data(expenses)
            
            # Generate requested insights
            insights = {}
            insight_functions = self.insight_types
            
            # If specific types are requested, only generate those
            if types and isinstance(types, list):
                insight_functions = {t: self.insight_types[t] for t in types if t in self.insight_types}
                
            # Generate each type of insight
            for insight_type, insight_function in insight_functions.items():
                insights[insight_type] = insight_function(df, user_data)
                
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {'error': str(e)}
    
    def _prepare_data(self, expenses):
        """
        Convert expense objects to DataFrame
        
        Args:
            expenses: List of expense objects
            
        Returns:
            Pandas DataFrame with expense data
        """
        processed_expenses = []
        
        for expense in expenses:
            # Process each expense into a dict
            processed_expense = {
                'id': getattr(expense, 'id', None),
                'amount': float(getattr(expense, 'amount', 0)),
                'category': getattr(expense, 'category', 'Uncategorized'),
                'date': getattr(expense, 'date', datetime.now()),
                'description': getattr(expense, 'description', ''),
            }
            processed_expenses.append(processed_expense)
            
        # Create DataFrame
        df = pd.DataFrame(processed_expenses)
        
        # Ensure date is datetime type
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
            # Add derived time fields
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day'] = df['date'].dt.day
            df['day_of_week'] = df['date'].dt.dayofweek
            df['week'] = df['date'].dt.isocalendar().week
            
        return df
        
    def _analyze_spending_patterns(self, df, user_data):
        """
        Analyze spending patterns over time
        
        Args:
            df: DataFrame with expense data
            user_data: User information for context
            
        Returns:
            List of insights about spending patterns
        """
        insights = []
        
        try:
            # Skip if not enough data
            if len(df) < 5:
                return [{"text": "Add more transactions to get spending pattern insights", "type": "info"}]
                
            # Monthly spending trends
            monthly_spending = df.groupby(['year', 'month'])['amount'].sum().reset_index()
            if len(monthly_spending) >= 2:
                monthly_spending['month_year'] = monthly_spending.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
                monthly_spending = monthly_spending.sort_values(['year', 'month'])
                
                # Calculate month-over-month change
                last_month = monthly_spending.iloc[-1]
                previous_month = monthly_spending.iloc[-2] if len(monthly_spending) > 1 else None
                
                if previous_month is not None:
                    change = last_month['amount'] - previous_month['amount']
                    change_percent = (change / previous_month['amount']) * 100 if previous_month['amount'] > 0 else 0
                    
                    if change_percent > 20:
                        insights.append({
                            "text": f"Your spending increased by {change_percent:.1f}% compared to last month",
                            "type": "alert",
                            "data": {
                                "current": float(last_month['amount']),
                                "previous": float(previous_month['amount']),
                                "change_percent": float(change_percent)
                            }
                        })
                    elif change_percent < -15:
                        insights.append({
                            "text": f"Great job! Your spending decreased by {-change_percent:.1f}% compared to last month",
                            "type": "success",
                            "data": {
                                "current": float(last_month['amount']),
                                "previous": float(previous_month['amount']),
                                "change_percent": float(change_percent)
                            }
                        })
            
            # Day of week spending
            dow_spending = df.groupby('day_of_week')['amount'].agg(['sum', 'count']).reset_index()
            if not dow_spending.empty and dow_spending['count'].sum() >= 10:
                max_dow = dow_spending.loc[dow_spending['sum'].idxmax()]
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                insights.append({
                    "text": f"You spend the most on {days[max_dow['day_of_week']]}s",
                    "type": "info",
                    "data": {
                        "day_of_week": days[max_dow['day_of_week']],
                        "amount": float(max_dow['sum']),
                        "transaction_count": int(max_dow['count'])
                    }
                })
                
            # Recent spending spike
            recent_cutoff = datetime.now() - timedelta(days=14)
            recent_df = df[df['date'] >= recent_cutoff]
            
            if len(recent_df) >= 5:
                recent_total = recent_df['amount'].sum()
                older_cutoff = recent_cutoff - timedelta(days=14)
                older_df = df[(df['date'] < recent_cutoff) & (df['date'] >= older_cutoff)]
                
                if len(older_df) >= 5:
                    older_total = older_df['amount'].sum()
                    change_percent = ((recent_total - older_total) / older_total) * 100 if older_total > 0 else 0
                    
                    if change_percent > 30:
                        insights.append({
                            "text": f"Your spending in the last 2 weeks increased by {change_percent:.1f}% compared to the previous 2 weeks",
                            "type": "alert",
                            "data": {
                                "recent_total": float(recent_total),
                                "previous_total": float(older_total),
                                "change_percent": float(change_percent)
                            }
                        })
                        
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {str(e)}")
            insights.append({"text": "Could not analyze spending patterns due to an error", "type": "error"})
            
        return insights
        
    def _analyze_categories(self, df, user_data):
        """
        Analyze spending by category
        
        Args:
            df: DataFrame with expense data
            user_data: User information for context
            
        Returns:
            List of insights about category spending
        """
        insights = []
        
        try:
            # Skip if not enough data
            if len(df) < 5:
                return [{"text": "Add more transactions to get category insights", "type": "info"}]
                
            # Top spending categories
            category_spending = df.groupby('category')['amount'].sum().reset_index()
            if not category_spending.empty:
                category_spending = category_spending.sort_values('amount', ascending=False)
                top_category = category_spending.iloc[0]
                total_spending = category_spending['amount'].sum()
                
                # Calculate percentage of total
                top_percent = (top_category['amount'] / total_spending) * 100 if total_spending > 0 else 0
                
                if top_percent > 40:
                    insights.append({
                        "text": f"{top_category['category']} accounts for {top_percent:.1f}% of your total spending",
                        "type": "alert" if top_percent > 50 else "info",
                        "data": {
                            "category": top_category['category'],
                            "amount": float(top_category['amount']),
                            "percent": float(top_percent)
                        }
                    })
                
                # Category comparison
                if len(category_spending) >= 3:
                    insights.append({
                        "text": f"Your top 3 expense categories are {category_spending.iloc[0]['category']}, {category_spending.iloc[1]['category']}, and {category_spending.iloc[2]['category']}",
                        "type": "info",
                        "data": {
                            "categories": category_spending.head(3)['category'].tolist(),
                            "amounts": category_spending.head(3)['amount'].tolist()
                        }
                    })
                    
            # Monthly category trends
            if 'month' in df.columns and 'year' in df.columns:
                # Get the most recent 3 months of data
                df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
                recent_months = sorted(df['year_month'].unique())[-3:]
                recent_data = df[df['year_month'].isin(recent_months)]
                
                if len(recent_data) >= 10:
                    # Find categories with significant increase
                    pivot = pd.pivot_table(
                        recent_data, 
                        values='amount', 
                        index='category', 
                        columns='year_month', 
                        aggfunc='sum'
                    ).fillna(0)
                    
                    if pivot.shape[1] >= 2:
                        # Compare latest month to previous
                        latest_month = pivot.columns[-1]
                        prev_month = pivot.columns[-2]
                        
                        # Calculate percent change for each category
                        pivot['change'] = ((pivot[latest_month] - pivot[prev_month]) / pivot[prev_month]) * 100
                        pivot = pivot.replace([np.inf, -np.inf], np.nan).dropna(subset=['change'])
                        
                        # Find categories with significant increase
                        increasing_cats = pivot[(pivot['change'] > 30) & (pivot[latest_month] > 100)]
                        
                        if not increasing_cats.empty:
                            top_increase = increasing_cats.sort_values('change', ascending=False).iloc[0]
                            insights.append({
                                "text": f"Your spending on {top_increase.name} increased by {top_increase['change']:.1f}% compared to last month",
                                "type": "alert",
                                "data": {
                                    "category": top_increase.name,
                                    "current": float(top_increase[latest_month]),
                                    "previous": float(top_increase[prev_month]),
                                    "change_percent": float(top_increase['change'])
                                }
                            })
                
        except Exception as e:
            logger.error(f"Error analyzing categories: {str(e)}")
            insights.append({"text": "Could not analyze category spending due to an error", "type": "error"})
            
        return insights
        
    def _find_unusual_transactions(self, df, user_data):
        """
        Identify unusual or outlier transactions
        
        Args:
            df: DataFrame with expense data
            user_data: User information for context
            
        Returns:
            List of insights about unusual transactions
        """
        insights = []
        
        try:
            # Skip if not enough data
            if len(df) < 10:
                return [{"text": "Add more transactions to identify unusual spending", "type": "info"}]
                
            # Find category outliers using Z-score
            category_groups = df.groupby('category')
            
            outliers = []
            for category, group in category_groups:
                if len(group) >= 5:  # Need at least 5 transactions to determine outliers
                    mean = group['amount'].mean()
                    std = group['amount'].std()
                    
                    if std > 0:  # Avoid division by zero
                        # Calculate Z-scores
                        z_scores = (group['amount'] - mean) / std
                        
                        # Find outliers (Z-score > 2.5)
                        category_outliers = group[z_scores > 2.5]
                        
                        # Only include recent outliers (last 60 days)
                        recent_cutoff = datetime.now() - timedelta(days=60)
                        recent_outliers = category_outliers[category_outliers['date'] >= recent_cutoff]
                        
                        outliers.extend(recent_outliers.to_dict('records'))
            
            # Sort outliers by amount (descending)
            outliers.sort(key=lambda x: x['amount'], reverse=True)
            
            # Generate insights for top outliers
            for i, outlier in enumerate(outliers[:3]):  # Limit to top 3 outliers
                date_str = outlier['date'].strftime('%b %d') if hasattr(outlier['date'], 'strftime') else str(outlier['date'])
                category = outlier['category']
                amount = outlier['amount']
                
                insights.append({
                    "text": f"Unusual spending: {amount:.2f} on {category} on {date_str}",
                    "type": "alert",
                    "data": {
                        "category": category,
                        "amount": float(amount),
                        "date": date_str,
                        "id": outlier.get('id', None)
                    }
                })
                
            # Highest single transaction in last 30 days
            recent_cutoff = datetime.now() - timedelta(days=30)
            recent_df = df[df['date'] >= recent_cutoff]
            
            if not recent_df.empty:
                max_transaction = recent_df.loc[recent_df['amount'].idxmax()]
                max_amount = max_transaction['amount']
                max_category = max_transaction['category']
                max_date = max_transaction['date'].strftime('%b %d') if hasattr(max_transaction['date'], 'strftime') else str(max_transaction['date'])
                
                insights.append({
                    "text": f"Your largest recent expense was {max_amount:.2f} on {max_category} ({max_date})",
                    "type": "info",
                    "data": {
                        "category": max_category,
                        "amount": float(max_amount),
                        "date": max_date,
                        "id": max_transaction.get('id', None)
                    }
                })
                
        except Exception as e:
            logger.error(f"Error finding unusual transactions: {str(e)}")
            insights.append({"text": "Could not identify unusual transactions due to an error", "type": "error"})
            
        return insights
        
    def _find_saving_opportunities(self, df, user_data):
        """
        Identify potential saving opportunities
        
        Args:
            df: DataFrame with expense data
            user_data: User information for context
            
        Returns:
            List of insights about saving opportunities
        """
        insights = []
        
        try:
            # Skip if not enough data
            if len(df) < 15:
                return [{"text": "Add more transactions to get saving recommendations", "type": "info"}]
                
            # Categories to analyze for potential savings
            saving_categories = [
                'Food & Dining', 'Entertainment', 'Shopping', 
                'Transportation', 'Utilities', 'Subscriptions'
            ]
            
            # Recent data (last 90 days)
            recent_cutoff = datetime.now() - timedelta(days=90)
            recent_df = df[df['date'] >= recent_cutoff]
            
            if len(recent_df) < 10:
                return [{"text": "Add more recent transactions to get saving recommendations", "type": "info"}]
                
            # Analyze each saving category
            for category in saving_categories:
                # Skip categories with insufficient data
                category_df = recent_df[recent_df['category'] == category]
                if len(category_df) < 5:
                    continue
                    
                # Calculate average weekly spending
                weeks_span = (recent_df['date'].max() - recent_df['date'].min()).days / 7
                if weeks_span < 1:
                    weeks_span = 1
                
                weekly_avg = category_df['amount'].sum() / weeks_span
                monthly_avg = weekly_avg * 4.33  # Convert to monthly
                
                # Thresholds by category (adjust based on typical spending)
                thresholds = {
                    'Food & Dining': 600,
                    'Entertainment': 300,
                    'Shopping': 500,
                    'Transportation': 400,
                    'Utilities': 350,
                    'Subscriptions': 100
                }
                
                threshold = thresholds.get(category, 500)  # Default threshold
                
                # Generate saving insight if spending exceeds threshold
                if monthly_avg > threshold:
                    potential_savings = monthly_avg - threshold
                    annual_savings = potential_savings * 12
                    
                    insights.append({
                        "text": f"You could save approximately {annual_savings:.2f} annually by reducing your {category} spending",
                        "type": "opportunity",
                        "data": {
                            "category": category,
                            "monthly_avg": float(monthly_avg),
                            "recommended_budget": float(threshold),
                            "monthly_savings": float(potential_savings),
                            "annual_savings": float(annual_savings)
                        }
                    })
                
            # Check for frequent small transactions
            small_transactions = recent_df[recent_df['amount'] < 15]
            if len(small_transactions) >= 10:
                small_monthly = len(small_transactions) / (weeks_span / 4.33)
                if small_monthly >= 15:
                    monthly_total = small_transactions['amount'].sum() / (weeks_span / 4.33)
                    insights.append({
                        "text": f"You're making approximately {small_monthly:.0f} small purchases per month, totaling around {monthly_total:.2f}",
                        "type": "opportunity",
                        "data": {
                            "monthly_count": float(small_monthly),
                            "monthly_total": float(monthly_total)
                        }
                    })
                
        except Exception as e:
            logger.error(f"Error finding saving opportunities: {str(e)}")
            insights.append({"text": "Could not identify saving opportunities due to an error", "type": "error"})
            
        return insights
        
    def _find_recurring_expenses(self, df, user_data):
        """
        Identify potential recurring expenses and subscriptions
        
        Args:
            df: DataFrame with expense data
            user_data: User information for context
            
        Returns:
            List of insights about recurring expenses
        """
        insights = []
        
        try:
            # Skip if not enough data
            if len(df) < 10:
                return [{"text": "Add more transactions to detect recurring expenses", "type": "info"}]
                
            # Keywords that suggest subscriptions
            subscription_keywords = [
                'subscription', 'monthly', 'netflix', 'spotify', 'amazon prime',
                'hulu', 'disney+', 'apple music', 'google play', 'youtube',
                'prime', 'membership', 'gym', 'fitness', 'club', 'streaming'
            ]
            
            # Find description patterns that appear in multiple months
            # Group by month-year and description
            if 'description' not in df.columns:
                return [{"text": "Transaction descriptions are needed to detect recurring expenses", "type": "info"}]
                
            # Convert descriptions to lowercase
            df['description_lower'] = df['description'].str.lower() if 'description' in df.columns else ''
            
            # Check for subscription keywords in description
            is_subscription = df['description_lower'].apply(
                lambda x: any(keyword in x for keyword in subscription_keywords) if isinstance(x, str) else False
            )
            potential_subscriptions = df[is_subscription]
            
            # Group by similar descriptions
            description_groups = defaultdict(list)
            
            for _, row in df.iterrows():
                desc = row.get('description_lower', '')
                if not isinstance(desc, str) or not desc:
                    continue
                    
                # Check for similar descriptions
                added = False
                for key in description_groups:
                    # Simple similarity check - could be improved with NLP
                    if (key in desc) or (desc in key) or (len(set(desc.split()) & set(key.split())) >= 2):
                        description_groups[key].append(row)
                        added = True
                        break
                        
                if not added:
                    description_groups[desc].append(row)
            
            # Find patterns that occur in multiple months with similar amounts
            recurring_expenses = []
            
            for desc, transactions in description_groups.items():
                if len(transactions) < 2:
                    continue
                    
                # Convert transactions to DataFrame
                group_df = pd.DataFrame(transactions)
                
                # Need at least 2 months to be recurring
                if 'date' in group_df.columns:
                    group_df['year_month'] = group_df['date'].dt.strftime('%Y-%m')
                    unique_months = group_df['year_month'].nunique()
                    
                    if unique_months >= 2:
                        # Check if amounts are similar
                        amount_std = group_df['amount'].std()
                        amount_mean = group_df['amount'].mean()
                        
                        if amount_mean > 0 and (amount_std / amount_mean) < 0.2:  # Low variance in amount
                            # This is likely a recurring expense
                            latest_date = group_df['date'].max()
                            recurring_expenses.append({
                                'description': desc,
                                'amount': amount_mean,
                                'frequency': unique_months / (group_df['date'].max() - group_df['date'].min()).days * 30,
                                'transactions': len(group_df),
                                'latest_date': latest_date
                            })
            
            # Sort by amount (descending)
            recurring_expenses.sort(key=lambda x: x['amount'], reverse=True)
            
            # Generate insights for top recurring expenses
            total_recurring = sum(expense['amount'] for expense in recurring_expenses)
            
            if recurring_expenses:
                insights.append({
                    "text": f"You have approximately {len(recurring_expenses)} recurring expenses totaling {total_recurring:.2f} per month",
                    "type": "info",
                    "data": {
                        "count": len(recurring_expenses),
                        "total": float(total_recurring)
                    }
                })
                
                # Details for top expenses
                for i, expense in enumerate(recurring_expenses[:3]):  # Limit to top 3
                    insights.append({
                        "text": f"Recurring expense: {expense['amount']:.2f} for {expense['description']}",
                        "type": "recurring",
                        "data": {
                            "description": expense['description'],
                            "amount": float(expense['amount']),
                            "frequency": float(expense['frequency']),
                            "transaction_count": expense['transactions']
                        }
                    })
                
        except Exception as e:
            logger.error(f"Error finding recurring expenses: {str(e)}")
            insights.append({"text": "Could not identify recurring expenses due to an error", "type": "error"})
            
        return insights 