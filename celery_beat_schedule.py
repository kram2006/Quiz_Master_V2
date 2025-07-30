from celery.schedules import crontab
from tasks import send_scheduled_reminders, send_monthly_reports, daily_maintenance

# Celery Beat Schedule Configuration
CELERY_BEAT_SCHEDULE = {
    # Send quiz reminders every 15 minutes
    'send-quiz-reminders': {
        'task': 'tasks.send_scheduled_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    
    # Send monthly reports on the first day of each month at 9 AM
    'send-monthly-reports': {
        'task': 'tasks.send_monthly_reports',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),  # 1st day of month at 9 AM
    },
    
    # Daily maintenance tasks at 2 AM
    'daily-maintenance': {
        'task': 'tasks.daily_maintenance',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Update quiz statistics every hour
    'update-quiz-statistics': {
        'task': 'tasks.update_quiz_statistics_task',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # Clean up incomplete attempts every 6 hours
    'cleanup-incomplete-attempts': {
        'task': 'tasks.cleanup_incomplete_attempts_task',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}

# Celery Beat Settings
CELERY_BEAT_SCHEDULE_FILENAME = 'celerybeat-schedule'
CELERY_BEAT_MAX_LOOP_INTERVAL = 300  # 5 minutes
CELERY_BEAT_SYNC_EVERY = 1  # Sync every task 