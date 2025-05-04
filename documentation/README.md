# Finance App Documentation

Welcome to the Finance App documentation. This directory contains comprehensive documentation for all components of the application.

## Core Files

- [app.py](./app.md) - Application entry point and configuration
- [config.py](./config.md) - Environment configuration settings
- [db.py](./db.md) - Database initialization

## Models

- [User](./models/user.md) - User authentication and profile
- [Expense](./models/expense.md) - Expense tracking
- [Income](./models/income.md) - Income management
- [Bill](./models/bill.md) - Bill tracking and reminders
- [Saving](./models/saving.md) - Savings goals
- [SavingTransaction](./models/saving_transaction.md) - Transactions for savings goals
- [AICorrection](./models/ai_correction.md) - AI expense category corrections

## Routes

- [Main Routes](./routes/main.md) - Web interface routes
- [Auth Routes](./routes/auth.md) - Authentication endpoints
- [API Routes](./routes/api.md) - General API endpoints
- [Expenses API](./routes/api_expenses.md) - Expense management API
- [Income API](./routes/api_income.md) - Income management API
- [Bills API](./routes/api_bills.md) - Bill management API
- [Savings API](./routes/api_savings.md) - Savings management API

## AI Modules

- [Expense Categorizer](./ai_modules/expense_categorizer.md) - AI-powered expense categorization

## Utility Modules

- [JSON Utilities](./utils/json_utils.md) - JSON handling utilities
- [Date Utilities](./utils/date_utils.md) - Date formatting and calculations

## Frontend

- [Templates](./templates/README.md) - HTML templates
- [Static Assets](./static/README.md) - CSS, JS, and images

## Deployment

- [Docker Configuration](../Dockerfile) - Docker containerization
- [Docker Compose](../docker-compose.yml) - Multi-container setup
- [Environment Variables](../.env.example) - Configuration variables

## Navigation

Each documentation file follows a consistent structure:
1. File path and basic description
2. Components (classes, functions, variables)
3. Usage examples
4. Related files 