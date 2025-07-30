# Quiz Master - Comprehensive Online Quiz Management System

A sophisticated web-based quiz management platform built with Python Flask that provides a complete solution for creating, administering, and taking online quizzes.

## 🚀 Features

### Core Features
- **Authentication System** - Secure user registration and login with role-based access
- **Quiz Management** - Create, edit, and manage quizzes with hierarchical organization
- **Quiz Taking** - Interactive quiz interface with timer and auto-submission
- **Analytics** - Comprehensive performance tracking and reporting

### Advanced Features
- **Email Notifications** - Automated quiz scheduling and reminder emails
- **CSV Export** - Download performance reports and user data
- **Background Processing** - Asynchronous task handling with Celery
- **Responsive Design** - Mobile-friendly interface using Bootstrap

## 🛠️ Technologies Used

### Backend
- **Python Flask** - Web framework
- **Flask-Login** - User authentication and session management
- **Flask-WTF** - Form handling and CSRF protection
- **Flask-Mail** - Email functionality
- **Flask-SQLAlchemy** - Database ORM

### Database
- **SQLite** - Database engine
- **SQLAlchemy** - Database ORM and query building

### Frontend
- **HTML/CSS/JavaScript** - Frontend technologies
- **Bootstrap** - CSS framework for responsive design
- **Vue.js** - Frontend framework for dynamic interactions

### Additional Libraries
- **WTForms** - Form validation and rendering
- **Email Validator** - Email validation
- **Celery** - Background task processing
- **Gunicorn** - WSGI server for production

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Git (for version control)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd Quizmaster
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   FLASK_APP=main.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

6. **Initialize the database**
   ```bash
   python main.py
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

The application will be available at `http://127.0.0.1:5000/`

## 👤 Default Admin Credentials

- **Email**: `admin@example.com`
- **Password**: `admin123`

## 📁 Project Structure

```
Quizmaster/
├── main.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── forms.py               # Form definitions
├── utils.py               # Utility functions
├── celery_app.py          # Background task processing
├── celery_beat_schedule.py # Scheduled tasks
├── cache.py               # Caching functionality
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
├── README.md             # Project documentation
├── instance/
│   └── quiz.db           # SQLite database
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       ├── script.js     # Main JavaScript
│       └── vue-app.js    # Vue.js components
└── templates/
    ├── base.html         # Base template
    ├── auth/            # Authentication templates
    ├── admin/           # Admin interface templates
    ├── user/            # User interface templates
    └── index.html       # Landing page
```

## 🔧 Configuration

### Email Configuration
Update the email settings in `config.py`:
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

### Database Configuration
The application uses SQLite by default. To use PostgreSQL or MySQL, update the database URI in `config.py`.

## 🎯 Usage

### For Administrators
1. Login with admin credentials
2. Create subjects and chapters
3. Add quizzes with questions and options
4. Schedule quizzes with time limits
5. Monitor user performance and generate reports

### For Users
1. Register for an account
2. Browse available quizzes
3. Take quizzes within the scheduled time
4. View performance history and analytics
5. Download personal performance reports

## 📊 Features in Detail

### Quiz Management
- **Hierarchical Organization**: Subject → Chapter → Quiz → Questions
- **CRUD Operations**: Full create, read, update, delete functionality
- **Scheduling**: Time-based quiz availability
- **Customization**: Configurable time limits and pass percentages

### Analytics & Reporting
- **Performance Tracking**: Individual and group performance metrics
- **CSV Export**: Downloadable performance reports
- **Trend Analysis**: Performance improvement over time
- **Subject Analytics**: Performance breakdown by subject

### Email System
- **Quiz Notifications**: Automated scheduling alerts
- **Reminder System**: Configurable reminder emails
- **Monthly Reports**: Automated performance summaries
- **Bulk Communications**: Mass email capabilities

## 🔒 Security Features

- **CSRF Protection**: Cross-site request forgery prevention
- **Password Hashing**: Secure password storage with bcrypt
- **Session Management**: Secure user sessions
- **Input Validation**: Comprehensive data sanitization
- **Role-Based Access**: Admin and user permission levels

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions, please open an issue in the GitHub repository.

## 🔄 Version History

- **v1.0.0** - Initial release with core quiz management features
- **v1.1.0** - Added email notifications and reporting
- **v1.2.0** - Enhanced analytics and user experience improvements

---

**Quiz Master** - Empowering education through intelligent quiz management.

