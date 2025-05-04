# User Model

## File Path
`/models/user.py`

## Description
This file defines the User model class for handling user accounts and authentication in the Finance App. It extends SQLAlchemy's Model class and Flask-Login's UserMixin for authentication functionality.

## Components

### Class: `User`

#### Base Classes
- `db.Model`: SQLAlchemy model base class
- `UserMixin`: Provides Flask-Login implementation

#### Attributes
- `id` (Integer): Primary key and unique identifier
- `name` (String): User's full name
- `email` (String): User's email address (unique)
- `password_hash` (String): Securely hashed password (never stores plain text)
- `salary` (Float): User's monthly default salary amount
- `created_at` (DateTime): Timestamp when the user account was created
- `is_admin` (Boolean): Flag indicating whether the user has admin privileges

#### Relationships
- `expenses`: One-to-many relationship with Expense model
- `savings`: One-to-many relationship with Saving model
- `bills`: One-to-many relationship with Bill model
- `incomes`: One-to-many relationship with Income model

#### Methods

##### `__init__(name, email, password, salary=0.0)`
- **Description**: Constructor to initialize a new user account
- **Parameters**:
  - `name`: User's full name
  - `email`: User's email address
  - `password`: Plain text password (will be hashed)
  - `salary`: User's monthly salary amount (defaults to 0.0)

##### `__repr__()`
- **Description**: Returns string representation of User object
- **Returns**: String in format `<User email@example.com>`

##### `set_password(password)`
- **Description**: Sets a new password by hashing it
- **Parameters**:
  - `password`: New password in plain text

##### `check_password(password)`
- **Description**: Verifies if a password matches the stored hash
- **Parameters**:
  - `password`: Password to check
- **Returns**: Boolean indicating if password matches

## Database Schema

The User model creates a 'users' table with the following structure:

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key, Auto Increment |
| name | String(100) | Not Null |
| email | String(120) | Unique, Not Null |
| password_hash | String(128) | Not Null |
| salary | Float | Not Null, Default 0.0 |
| created_at | DateTime | Default Current Timestamp |
| is_admin | Boolean | Default False |

## Usage Examples

### Creating a new user
```python
new_user = User(
    name="John Doe",
    email="john.doe@example.com",
    password="securepassword123",
    salary=5000.00
)
db.session.add(new_user)
db.session.commit()
```

### Authenticating a user
```python
user = User.query.filter_by(email=email).first()
if user and user.check_password(password):
    # User is authenticated
    login_user(user)
else:
    # Authentication failed
    flash("Invalid email or password")
```

### Updating a user's password
```python
user = User.query.get(user_id)
user.set_password(new_password)
db.session.commit()
```

## Related Files

- [app.py](../app.md) - User authentication configuration
- [routes/auth.py](../routes/auth.md) - Authentication endpoints
- [models/expense.py](./expense.md) - Related through user relationship
- [models/saving.py](./saving.md) - Related through user relationship
- [models/bill.py](./bill.md) - Related through user relationship
- [models/income.py](./income.md) - Related through user relationship

## Navigation

- [Back to Models Documentation](./README.md)
- [Back to Main Documentation](../README.md)
- [Routes Documentation](../routes/README.md) 