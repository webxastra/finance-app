# Static Assets Documentation

This directory contains documentation for the static assets used in the Finance App's web interface.

## Asset Structure

- [CSS](./css.md) - Stylesheets for the application
- [JavaScript](./js.md) - Frontend functionality
- [Images](./images.md) - Icons, logos, and UI elements
- [Vendor](./vendor.md) - Third-party libraries

## CSS Architecture

The application uses a modular CSS approach:

1. **Base Styles** (`css/base.css`):
   - Typography
   - Color variables
   - Global element styles

2. **Component Styles** (`css/components/`):
   - Forms
   - Buttons
   - Cards
   - Navigation

3. **Section Styles** (`css/sections/`):
   - Dashboard
   - Expenses
   - Income
   - Bills
   - Savings

## JavaScript Organization

The JavaScript is organized into:

1. **Core Functionality** (`js/core/`):
   - API client
   - Form handling
   - Authentication
   - Utility functions

2. **Feature Modules** (`js/features/`):
   - Dashboard
   - Expenses
   - Income
   - Bills
   - Savings

3. **Visualizations** (`js/charts/`):
   - Spending charts
   - Budget charts
   - Savings progress
   - Income vs expenses

## Third-Party Dependencies

- Bootstrap 5
- Chart.js
- FontAwesome
- Moment.js
- SortableJS

## Navigation

- [Back to Main Documentation](../README.md)
- [Templates Documentation](../templates/README.md)
- [Routes Documentation](../routes/README.md) 