# Expense Model

## File Path
`/models/expense.py`

## Description
This file defines the Expense model class for tracking and categorizing user expenses in the Finance App. It enables users to record, categorize, and analyze their spending patterns.

## Components

### Class: `Expense`

#### Base Classes
- `db.Model`: SQLAlchemy model base class

#### Attributes
- `id` (Integer): Primary key and unique identifier
- `amount` (Float): The expense amount
- `description` (String): Description of the expense
- `category` (String): Category of the expense (e.g., "Food", "Transport")
- `date` (Date): Date when the expense occurred
- `payment_method` (String): Method of payment (e.g., "Cash", "Credit Card")
- `is_recurring` (Boolean): Whether this is a recurring expense
- `created_at` (DateTime): Timestamp when the expense was created
- `updated_at` (DateTime): Timestamp when the expense was last updated
- `user_id` (Integer): Foreign key to the User model

#### Relationships
- `user`: Many-to-one relationship with User model
- `ai_corrections`: One-to-many relationship with AICorrection model

#### Methods

##### `__init__(amount, description, category, date, user_id, payment_method="Credit Card", is_recurring=False)`
- **Description**: Constructor to initialize a new expense
- **Parameters**:
  - `amount`: Expense amount
  - `description`: Description of the expense
  - `category`: Category of the expense
  - `date`: Date of the expense
  - `user_id`: ID of the user who owns this expense
  - `payment_method`: Method of payment (defaults to "Credit Card")
  - `is_recurring`: Flag for recurring expenses (defaults to False)

##### `__repr__()`
- **Description**: Returns string representation of Expense object
- **Returns**: String in format `<Expense $amount - description>`

##### `to_dict()`
- **Description**: Converts the expense to a dictionary for API responses
- **Returns**: Dictionary with expense data

##### `from_dict(data, user_id)`
- **Description**: Static method to create an Expense from dictionary data
- **Parameters**:
  - `data`: Dictionary with expense data
  - `user_id`: ID of the user who owns this expense
- **Returns**: New Expense instance

## Database Schema

The Expense model creates an 'expenses' table with the following structure:

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key, Auto Increment |
| amount | Float | Not Null |
| description | String(255) | Not Null |
| category | String(100) | Not Null |
| date | Date | Not Null |
| payment_method | String(50) | Not Null |
| is_recurring | Boolean | Not Null, Default False |
| created_at | DateTime | Default Current Timestamp |
| updated_at | DateTime | Default Current Timestamp, OnUpdate Current Timestamp |
| user_id | Integer | Foreign Key (users.id), Not Null |

## Usage Examples

### Creating a new expense
```python
new_expense = Expense(
    amount=25.50,
    description="Grocery shopping",
    category="Food",
    date=datetime.date.today(),
    user_id=current_user.id,
    payment_method="Credit Card"
)
db.session.add(new_expense)
db.session.commit()
```

### Querying expenses by category
```python
food_expenses = Expense.query.filter_by(
    user_id=current_user.id,
    category="Food"
).order_by(Expense.date.desc()).all()
```

### Updating an expense
```python
expense = Expense.query.get(expense_id)
expense.amount = 30.00
expense.category = "Groceries"
db.session.commit()
```

## Related Files

- [models/user.py](./user.md) - User relationship
- [models/ai_correction.py](./ai_correction.md) - AI classification corrections
- [routes/api_expenses.py](../routes/api_expenses.md) - Expense API endpoints
- [ai_modules/expense_categorizer.md](../ai_modules/expense_categorizer.md) - AI categorization

## Navigation

- [Back to Models Documentation](./README.md)
- [Back to Main Documentation](../README.md)
- [User Model](./user.md) 