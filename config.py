import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///quiz.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration - Gmail with App Password
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'krish78790@gmail.com'
    MAIL_PASSWORD = 'edkrbffbaapursgn'
    MAIL_DEFAULT_SENDER = 'krish78790@gmail.com'
    
    # Quiz Notification Settings
    SEND_QUIZ_NOTIFICATIONS = True
    SEND_REMINDERS = True
    REMINDER_HOURS_BEFORE = 1  # Send reminder 1 hour before quiz starts