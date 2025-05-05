# Finance App

<div align="center">
  <img src="static/img/logo.png" alt="Finance App Logo" width="200" height="auto">
  <p><strong>Personal Finance Management with AI-Powered Insights</strong></p>
</div>

## 📋 Overview

Finance App is a comprehensive personal finance management system built with Flask and enhanced with AI capabilities. It helps users track expenses, manage income, plan savings, and monitor bills with intuitive visualizations and smart categorization.

### Key Features

- 📊 **Expense Tracking**: Log and categorize your expenses
- 💰 **Income Management**: Track multiple income sources
- 🔔 **Bill Reminders**: Never miss a payment
- 💸 **Savings Goals**: Set and track progress towards financial goals
- 🤖 **AI-Powered Categorization**: Automatic expense classification
- 📈 **Financial Insights**: Visualize spending patterns
- 📱 **Responsive Interface**: Access from any device

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite
- Node.js and npm (for frontend assets)

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/webxastra/finance-app.git
   cd finance-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```bash
   flask run
   ```

### Docker Deployment

For containerized deployment:

```bash
docker-compose up -d
```

After deployment, access the application in your web browser at:

```
http://localhost:8000
```

The PostgreSQL database will be accessible on port 5433.

### Docker Commands Reference

```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose build
```

## 🏗️ Project Structure

```
finance-app/
├── ai_modules/         # AI-powered expense categorization
├── app.py              # Application entry point
├── config.py           # Configuration settings
├── db.py               # Database initialization
├── documentation/      # Comprehensive documentation
├── models/             # Database models
├── routes/             # API and web routes
├── static/             # CSS, JS, and assets
├── templates/          # HTML templates
├── utils/              # Utility functions
├── migrations/         # Database migrations
└── instance/           # Instance-specific data
```

## 💡 AI-Powered Features

The application uses machine learning to provide smart expense categorization:

- **Automatic Classification**: Expenses are categorized based on their descriptions
- **Learning System**: Improves accuracy over time with user feedback
- **Confidence Scoring**: Identifies uncertain predictions for manual review

## 🔧 Technology Stack

- **Backend**: Flask, SQLAlchemy, Alembic
- **Database**: PostgreSQL (recommended), SQLite (development)
- **Frontend**: Bootstrap, Chart.js, jQuery
- **AI/ML**: scikit-learn, NLTK
- **Authentication**: Flask-Login, JWT
- **Deployment**: Docker, Gunicorn

## 📖 Documentation

Comprehensive documentation is available in the `/documentation` directory, covering:

- Core application components
- Database models
- API endpoints
- AI modules
- Frontend templates
- Deployment options

## 🚧 Roadmap

- [ ] Mobile application integration
- [ ] Budgeting features
- [ ] Financial goal recommendations
- [ ] Multi-currency support
- [ ] Advanced reporting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**WebXastra** - [GitHub Profile](https://github.com/webxastra)

---

<div align="center">
  <p>Made with ❤️ for better financial management</p>
</div>
