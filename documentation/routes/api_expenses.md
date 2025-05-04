# Expenses API Routes

## File Path
`/routes/api_expenses.py`

## Description
This file defines the API endpoints for managing expenses in the Finance App. It provides routes for creating, reading, updating, and deleting expenses, as well as for expense analytics and categorization.

## Components

### Blueprint

- **Name**: `expenses_api`
- **URL Prefix**: `/api/expenses`
- **Import Path**: `from routes import expenses_api`

### Routes

#### `GET /api/expenses`
- **Function**: `get_expenses()`
- **Description**: Retrieves expenses for the authenticated user
- **URL Parameters**:
  - `page` (int, optional): Page number for pagination (default: 1)
  - `per_page` (int, optional): Number of items per page (default: 20)
  - `category` (str, optional): Filter by category
  - `start_date` (date, optional): Filter by start date
  - `end_date` (date, optional): Filter by end date
  - `sort` (str, optional): Sort field (default: 'date')
  - `order` (str, optional): Sort order ('asc' or 'desc', default: 'desc')
- **Response**: JSON array of expense objects with pagination metadata
- **Authentication**: Required
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `400`: Bad request (invalid parameters)

#### `POST /api/expenses`
- **Function**: `create_expense()`
- **Description**: Creates a new expense
- **Request Body**:
  - `amount` (float, required): Expense amount
  - `description` (str, required): Description of the expense
  - `category` (str, required): Category of the expense
  - `date` (date, required): Date of the expense
  - `payment_method` (str, optional): Method of payment
  - `is_recurring` (bool, optional): Whether it's a recurring expense
- **Response**: JSON object with the created expense
- **Authentication**: Required
- **Status Codes**:
  - `201`: Created
  - `400`: Bad request (invalid data)
  - `401`: Unauthorized

#### `GET /api/expenses/<int:id>`
- **Function**: `get_expense(id)`
- **Description**: Retrieves a specific expense by ID
- **URL Parameters**:
  - `id` (int, required): Expense ID
- **Response**: JSON object with the expense details
- **Authentication**: Required
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Not found

#### `PUT /api/expenses/<int:id>`
- **Function**: `update_expense(id)`
- **Description**: Updates a specific expense
- **URL Parameters**:
  - `id` (int, required): Expense ID
- **Request Body**:
  - `amount` (float, optional): Updated expense amount
  - `description` (str, optional): Updated description
  - `category` (str, optional): Updated category
  - `date` (date, optional): Updated date
  - `payment_method` (str, optional): Updated payment method
  - `is_recurring` (bool, optional): Updated recurring status
- **Response**: JSON object with the updated expense
- **Authentication**: Required
- **Status Codes**:
  - `200`: Success
  - `400`: Bad request (invalid data)
  - `401`: Unauthorized
  - `404`: Not found

#### `DELETE /api/expenses/<int:id>`
- **Function**: `delete_expense(id)`
- **Description**: Deletes a specific expense
- **URL Parameters**:
  - `id` (int, required): Expense ID
- **Response**: JSON confirmation of deletion
- **Authentication**: Required
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized
  - `404`: Not found

#### `GET /api/expenses/categories`
- **Function**: `get_expense_categories()`
- **Description**: Retrieves expense categories with totals
- **URL Parameters**:
  - `start_date` (date, optional): Filter by start date
  - `end_date` (date, optional): Filter by end date
- **Response**: JSON array of category objects with totals
- **Authentication**: Required
- **Status Codes**:
  - `200`: Success
  - `401`: Unauthorized

## Usage Examples

### Getting all expenses
```bash
curl -X GET "http://localhost:5000/api/expenses?page=1&per_page=10&category=Food" \
  -H "Authorization: Bearer {token}"
```

### Creating a new expense
```bash
curl -X POST "http://localhost:5000/api/expenses" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 25.50,
    "description": "Grocery shopping",
    "category": "Food",
    "date": "2023-05-15",
    "payment_method": "Credit Card"
  }'
```

### Updating an expense
```bash
curl -X PUT "http://localhost:5000/api/expenses/123" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 30.00,
    "category": "Groceries"
  }'
```

## Related Files

- [models/expense.py](../models/expense.md) - Expense model
- [routes/api.py](./api.md) - Core API functionality
- [ai_modules/expense_categorizer.md](../ai_modules/expense_categorizer.md) - AI categorization
- [utils/json_utils.md](../utils/json_utils.md) - JSON handling utilities

## Navigation

- [Back to Routes Documentation](./README.md)
- [Back to Main Documentation](../README.md)
- [Expense Model](../models/expense.md) 