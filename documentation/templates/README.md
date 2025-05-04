# Templates Documentation

This directory contains documentation for the HTML templates used in the Finance App's web interface.

## Template Structure

- [Layouts](./layouts.md) - Base template layouts and common elements
- [Auth Templates](./auth.md) - Authentication-related templates
- [Dashboard](./dashboard.md) - Main dashboard and overview
- [Expenses](./expenses.md) - Expense management templates
- [Income](./income.md) - Income management templates
- [Bills](./bills.md) - Bill management templates
- [Savings](./savings.md) - Savings goals templates
- [Reports](./reports.md) - Financial reporting templates

## Template Architecture

The application uses Jinja2 templates with a hierarchical structure:

1. **Base Layout** (`layouts/base.html`):
   - Contains common HTML structure
   - Includes CSS and JavaScript
   - Defines navigation and footer

2. **Section Layouts**:
   - Extend base layout
   - Define section-specific elements
   - Include common elements for each feature area

3. **Feature Templates**:
   - Extend section layouts
   - Implement specific features
   - Include forms and interactive elements

## Frontend Technologies

The templates utilize:
- **Bootstrap 5**: For responsive design
- **Chart.js**: For data visualization
- **FontAwesome**: For icons
- **Custom CSS**: For application-specific styling

## JavaScript Integration

- Form validation and submission
- AJAX for dynamic content loading
- Chart rendering and updates
- Interactive budget management

## Navigation

- [Back to Main Documentation](../README.md)
- [Static Assets Documentation](../static/README.md)
- [Routes Documentation](../routes/README.md) 