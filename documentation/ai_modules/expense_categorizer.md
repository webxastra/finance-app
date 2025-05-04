# AI Expense Categorizer

## File Path
`/ai_modules/expense_categorizer/`

## Description
This module provides AI-powered expense categorization functionality for the Finance App. It uses natural language processing (NLP) and machine learning to automatically categorize expenses based on their descriptions.

## Components

### Classes

#### `AITrainer`
- **File**: `ai_trainer.py`
- **Description**: Manages the training and fine-tuning of the expense categorization model
- **Methods**:
  - `train_initial_model()`: Trains the initial model with default data
  - `retrain_model(corrections)`: Retrains the model with user corrections
  - `save()`: Saves the current model to disk
  - `load()`: Loads a saved model from disk

#### `ExpenseCategorizer`
- **File**: `categorizer.py`
- **Description**: Classifies expense descriptions into categories
- **Methods**:
  - `predict(description)`: Predicts the category for an expense description
  - `predict_batch(descriptions)`: Predicts categories for multiple descriptions
  - `get_confidence(description)`: Returns prediction confidence score

#### `TextProcessor`
- **File**: `text_processor.py`
- **Description**: Handles text preprocessing for the ML model
- **Methods**:
  - `tokenize(text)`: Splits text into tokens
  - `clean_text(text)`: Removes special characters and normalizes text
  - `extract_features(text)`: Extracts features for classification

### Routes

#### `ai_expense` Blueprint
- **URL Prefix**: `/api/ai/expenses`
- **Routes**:
  - `POST /api/ai/expenses/categorize`: Categorize an expense description
  - `POST /api/ai/expenses/feedback`: Submit feedback on categorization
  - `GET /api/ai/expenses/categories`: Get available expense categories
  - `POST /api/ai/expenses/retrain`: Trigger model retraining (admin only)

## AI Technology

### Machine Learning Models
- **Primary Model**: Multinomial Naive Bayes
- **Alternative Models**: SVM, Random Forest
- **Feature Extraction**: TF-IDF Vectorization
- **NLP Processing**: Using NLTK/spaCy for tokenization and lemmatization

### Training Data
- Initial training data from common expense categories
- User corrections to improve accuracy over time
- Historical expense data (anonymized)

### Performance Metrics
- Accuracy: ~85-90% on typical expense descriptions
- Confidence scoring to identify uncertain predictions
- Continuous improvement through user feedback

## Usage Examples

### Categorizing an expense via API
```bash
curl -X POST "http://localhost:5000/api/ai/expenses/categorize" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Starbucks coffee"
  }'
```

### Programmatic usage
```python
from ai_modules.expense_categorizer.categorizer import ExpenseCategorizer

categorizer = ExpenseCategorizer()
category = categorizer.predict("Grocery shopping at Walmart")
print(f"Predicted category: {category}")
```

### Training the model
```python
from ai_modules.expense_categorizer.ai_trainer import AITrainer

trainer = AITrainer()
trainer.train_initial_model()
```

## Related Files

- [models/expense.py](../models/expense.md) - Expense model
- [models/ai_correction.py](../models/ai_correction.md) - AI correction model
- [routes/api_expenses.py](../routes/api_expenses.md) - Expense API endpoints

## Navigation

- [Back to AI Modules Documentation](./README.md)
- [Back to Main Documentation](../README.md)
- [Models Documentation](../models/README.md) 