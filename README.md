# Finance App

A comprehensive personal finance management application built with Flask, SQLAlchemy, and AI-powered expense categorization.

## Features

- **Expense Tracking**: Record and categorize your daily expenses
- **Income Management**: Track multiple income sources
- **Bills Management**: Never miss a bill payment with reminders
- **Savings Goals**: Set and track progress towards financial goals
- **AI-Powered Categorization**: Automatic categorization of expenses using machine learning
- **Data Visualization**: Visual representations of spending habits
- **Secure Authentication**: User account system with secure login
- **API Access**: Full REST API for programmatic access
- **Responsive Design**: Works on desktop and mobile devices

## Technologies Used

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Production database (SQLite for development)
- **Flask-Login**: User authentication
- **Flask-Migrate**: Database migrations
- **Gunicorn**: WSGI HTTP Server for production

### Data Science & ML
- **Pandas**: Data analysis
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning for expense categorization
- **Matplotlib**: Data visualization
- **NLTK/Spacy**: Natural language processing

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container management
- **Gunicorn**: Production WSGI server

## Setup Instructions

### Standard Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/financeapp.git
   cd financeapp
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Edit `.env` with your configurations
   ```bash
   cp .env.example .env
   ```

5. **Initialize the database**:
   ```bash
   flask db upgrade
   ```

6. **Run the application**:
   ```bash
   flask run
   ```

### Docker Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/financeapp.git
   cd financeapp
   ```

2. **Create environment file**:
   - Copy `.env.example` to `.env`
   - Edit `.env` with your configurations
   ```bash
   cp .env.example .env
   ```

3. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Open your browser and go to `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login and get access token
- `GET /api/auth/profile`: Get current user profile

### Expenses
- `GET /api/expenses`: List expenses
- `POST /api/expenses`: Create new expense
- `GET /api/expenses/<id>`: Get expense details
- `PUT /api/expenses/<id>`: Update expense
- `DELETE /api/expenses/<id>`: Delete expense

### Income
- `GET /api/income`: List income sources
- `POST /api/income`: Add new income
- `GET /api/income/<id>`: Get income details
- `PUT /api/income/<id>`: Update income source
- `DELETE /api/income/<id>`: Delete income source

### Bills
- `GET /api/bills`: List bills
- `POST /api/bills`: Add new bill
- `GET /api/bills/<id>`: Get bill details
- `PUT /api/bills/<id>`: Update bill
- `DELETE /api/bills/<id>`: Delete bill

### Savings
- `GET /api/savings`: List savings goals
- `POST /api/savings`: Create new savings goal
- `GET /api/savings/<id>`: Get savings goal details
- `PUT /api/savings/<id>`: Update savings goal
- `DELETE /api/savings/<id>`: Delete savings goal
- `POST /api/savings/<id>/transactions`: Add transaction to savings goal

## Folder Structure

```
financeapp/
├── app.py                  # Application entry point
├── config.py               # Configuration settings
├── db.py                   # Database initialization
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Example environment variables
├── ai_modules/             # AI/ML modules
│   └── expense_categorizer/
├── models/                 # Database models
│   ├── __init__.py
│   ├── user.py
│   ├── expense.py
│   ├── income.py
│   ├── bill.py
│   ├── saving.py
│   └── ...
├── routes/                 # API and web routes
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── api.py
│   └── ...
├── static/                 # Static files (CSS, JS)
├── templates/              # HTML templates
├── utils/                  # Utility functions
└── documentation/          # Documentation files
```

## Screenshots

![Dashboard](/path/to/dashboard-screenshot.png)
*Dashboard with expense overview and charts*

![Expense Management](/path/to/expense-screenshot.png)
*Expense management interface*

![Savings Goals](/path/to/savings-screenshot.png)
*Savings goals tracking*

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask and SQLAlchemy teams for their excellent documentation
- The open-source community for various libraries used
- All contributors to this project 