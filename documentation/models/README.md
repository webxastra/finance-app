# Models Documentation

This directory contains documentation for all database models used in the Finance App.

## Database Models

- [User](./user.md) - User authentication and profile management
- [Expense](./expense.md) - Expense tracking and categorization
- [Income](./income.md) - Income sources and tracking
- [Bill](./bill.md) - Bill management and reminders
- [Saving](./saving.md) - Savings goals tracking
- [SavingTransaction](./saving_transaction.md) - Transactions for savings goals
- [AICorrection](./ai_correction.md) - AI expense categorization corrections

## Database Schema Overview

The application uses SQLAlchemy ORM with the following relationships:

- **User** has many **Expenses**, **Incomes**, **Bills**, and **Savings**
- **Saving** has many **SavingTransactions**
- **AICorrection** is used to improve expense categorization over time

## Common Model Features

All models include:
- Primary key (id)
- Creation/modification timestamps
- User relationship (except for system models)
- SQLAlchemy relationships to related models
- JSON serialization methods

## Navigation

- [Back to Main Documentation](../README.md)
- [Routes Documentation](../routes/README.md)
- [AI Modules Documentation](../ai_modules/README.md) 