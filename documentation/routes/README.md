# Routes Documentation

This directory contains documentation for all route blueprints used in the Finance App.

## API Routes

- [API](./api.md) - Core API functionality and shared endpoints
- [Expenses API](./api_expenses.md) - Expense management endpoints
- [Income API](./api_income.md) - Income management endpoints
- [Bills API](./api_bills.md) - Bill management endpoints
- [Savings API](./api_savings.md) - Savings management endpoints

## Web Routes

- [Main Routes](./main.md) - Primary web interface pages
- [Auth Routes](./auth.md) - Authentication and user management

## API Overview

The application provides a RESTful API for all financial operations:

| Resource Type | Endpoints | Description |
|---------------|-----------|-------------|
| Authentication | `/api/auth/*` | User registration, login, profile |
| Expenses | `/api/expenses/*` | CRUD operations for expenses |
| Income | `/api/income/*` | CRUD operations for income sources |
| Bills | `/api/bills/*` | CRUD operations for bills |
| Savings | `/api/savings/*` | CRUD operations for savings goals |
| Analytics | `/api/analytics/*` | Financial analytics and reporting |

## Common Route Features

All API routes:
- Return JSON responses
- Use consistent error handling
- Require authentication (except login/register)
- Include pagination for list endpoints
- Support filtering and sorting

## Navigation

- [Back to Main Documentation](../README.md)
- [Models Documentation](../models/README.md)
- [Utils Documentation](../utils/README.md) 