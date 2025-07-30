from celery import current_task
from celery_app import celery
from flask_mail import Mail, Message
from models import db, User, Quiz, QuizAttempt
from datetime import datetime, timedelta
import csv
import io
import json
from config import Config

# Initialize Flask app context for tasks
from main import app

@celery.task(bind=True)
def send_quiz_notification_task(self, quiz_id, user_ids):
    """Send quiz notification emails as a background task"""
    try:
        with app.app_context():
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return {'status': 'error', 'message': 'Quiz not found'}
            
            users = User.query.filter(User.id.in_(user_ids)).all()
            
            # Email configuration
            mail = Mail(app)
            
            subject = f"Quiz Scheduled: {quiz.title}"
            start_time = quiz.start_datetime.strftime("%B %d, %Y at %I:%M %p") if quiz.start_datetime else "TBD"
            end_time = quiz.end_datetime.strftime("%B %d, %Y at %I:%M %p") if quiz.end_datetime else "TBD"
            time_limit = f"{quiz.time_limit} minutes" if quiz.time_limit else "No time limit"
            
            body = f"""
            Hello!

            A new quiz has been scheduled for you:

            Quiz: {quiz.title}
            Chapter: {quiz.chapter.name}
            Subject: {quiz.chapter.subject.name}
            Start Time: {start_time}
            End Time: {end_time}
            Time Limit: {time_limit}
            Pass Percentage: {quiz.pass_percentage}%

            Description: {quiz.description or 'No description provided'}

            Please log in to your account to take the quiz during the scheduled time.

            Best regards,
            Quiz Master Team
            """
            
            success_count = 0
            failed_emails = []
            
            for user in users:
                if not user.is_admin:
                    try:
                        msg = Message(
                            subject=subject,
                            recipients=[user.email],
                            body=body
                        )
                        mail.send(msg)
                        success_count += 1
                        
                        # Update task progress
                        self.update_state(
                            state='PROGRESS',
                            meta={'current': success_count, 'total': len(users), 'status': 'Sending emails...'}
                        )
                        
                    except Exception as e:
                        failed_emails.append({'email': user.email, 'error': str(e)})
            
            return {
                'status': 'success',
                'sent': success_count,
                'failed': len(failed_emails),
                'failed_emails': failed_emails
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def send_quiz_reminder_task(self, quiz_id, user_ids):
    """Send quiz reminder emails as a background task"""
    try:
        with app.app_context():
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return {'status': 'error', 'message': 'Quiz not found'}
            
            users = User.query.filter(User.id.in_(user_ids)).all()
            
            mail = Mail(app)
            
            subject = f"Reminder: Quiz '{quiz.title}' starts in 1 hour!"
            start_time = quiz.start_datetime.strftime("%B %d, %Y at %I:%M %p")
            end_time = quiz.end_datetime.strftime("%B %d, %Y at %I:%M %p") if quiz.end_datetime else "TBD"
            
            body = f"""
            Hello!

            This is a reminder that your quiz starts in 1 hour:

            Quiz: {quiz.title}
            Chapter: {quiz.chapter.name}
            Subject: {quiz.chapter.subject.name}
            Start Time: {start_time}
            End Time: {end_time}

            Please make sure you're ready to take the quiz!

            Best regards,
            Quiz Master Team
            """
            
            success_count = 0
            failed_emails = []
            
            for user in users:
                if not user.is_admin:
                    try:
                        msg = Message(
                            subject=subject,
                            recipients=[user.email],
                            body=body
                        )
                        mail.send(msg)
                        success_count += 1
                        
                        self.update_state(
                            state='PROGRESS',
                            meta={'current': success_count, 'total': len(users), 'status': 'Sending reminders...'}
                        )
                        
                    except Exception as e:
                        failed_emails.append({'email': user.email, 'error': str(e)})
            
            return {
                'status': 'success',
                'sent': success_count,
                'failed': len(failed_emails),
                'failed_emails': failed_emails
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def send_monthly_report_task(self, user_id):
    """Send monthly performance report to a specific user"""
    try:
        with app.app_context():
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            # Get current month and year
            now = datetime.utcnow()
            current_month = now.month
            current_year = now.year
            
            # Get attempts from current month
            attempts = QuizAttempt.query.filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.date_taken >= datetime(current_year, current_month, 1),
                QuizAttempt.date_taken < datetime(current_year, current_month + 1, 1) if current_month < 12 else datetime(current_year + 1, 1, 1)
            ).order_by(QuizAttempt.date_taken.desc()).all()
            
            if not attempts:
                return {'status': 'no_data', 'message': 'No attempts this month'}
            
            # Calculate statistics
            total_attempts = len(attempts)
            passed_attempts = sum(1 for attempt in attempts if attempt.passed)
            failed_attempts = total_attempts - passed_attempts
            avg_score = sum(attempt.score for attempt in attempts if attempt.score) / total_attempts if total_attempts > 0 else 0
            highest_score = max((attempt.score for attempt in attempts if attempt.score), default=0)
            
            # Get subject breakdown
            subject_stats = {}
            for attempt in attempts:
                subject_name = attempt.quiz.chapter.subject.name
                if subject_name not in subject_stats:
                    subject_stats[subject_name] = {'attempts': 0, 'scores': []}
                subject_stats[subject_name]['attempts'] += 1
                if attempt.score:
                    subject_stats[subject_name]['scores'].append(attempt.score)
            
            # Calculate subject averages
            subject_averages = {}
            for subject, stats in subject_stats.items():
                if stats['scores']:
                    subject_averages[subject] = sum(stats['scores']) / len(stats['scores'])
            
            # Create email content
            month_name = now.strftime('%B %Y')
            subject = f"Your Monthly Quiz Report - {month_name}"
            
            body = f"""
            Hello {user.name}!

            Here's your monthly quiz performance report for {month_name}:

            📊 OVERALL PERFORMANCE
            • Total Quizzes Taken: {total_attempts}
            • Passed: {passed_attempts}
            • Failed: {failed_attempts}
            • Pass Rate: {(passed_attempts/total_attempts*100):.1f}%
            • Average Score: {avg_score:.1f}%
            • Highest Score: {highest_score:.1f}%

            📚 SUBJECT BREAKDOWN
            """
            
            for subject_name, avg_score in subject_averages.items():
                body += f"• {subject_name}: {avg_score:.1f}%\n"
            
            body += f"""
            📅 RECENT ACTIVITY
            """
            
            # Add recent attempts
            for attempt in attempts[:5]:  # Last 5 attempts
                quiz = attempt.quiz
                chapter = quiz.chapter
                subject_name = chapter.subject.name
                status = "PASS" if attempt.passed else "FAIL"
                body += f"• {quiz.title} ({subject_name}): {attempt.score:.1f}% - {status}\n"
            
            body += f"""
            Keep up the great work! Continue practicing to improve your scores.

            Best regards,
            Quiz Master Team
            """
            
            # Send email
            mail = Mail(app)
            msg = Message(
                subject=subject,
                recipients=[user.email],
                body=body
            )
            mail.send(msg)
            
            return {
                'status': 'success',
                'user_email': user.email,
                'attempts_count': total_attempts,
                'avg_score': avg_score
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def generate_performance_report_task(self, user_ids=None, format='csv'):
    """Generate performance reports for users as a background task"""
    try:
        with app.app_context():
            if user_ids:
                users = User.query.filter(User.id.in_(user_ids)).all()
            else:
                users = User.query.filter_by(is_admin=False).all()
            
            if not users:
                return {'status': 'error', 'message': 'No users found'}
            
            # Get all quiz attempts for these users
            all_attempts = []
            for user in users:
                attempts = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.date_taken.desc()).all()
                all_attempts.extend(attempts)
            
            if format == 'csv':
                # Create CSV data
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['User Name', 'User Email', 'Quiz Title', 'Subject', 'Chapter', 'Score (%)', 'Status', 'Time Limit (min)', 'Pass Percentage', 'Date/Time'])
                
                # Write data
                for attempt in all_attempts:
                    quiz = attempt.quiz
                    chapter = quiz.chapter
                    subject = chapter.subject
                    user = User.query.get(attempt.user_id)
                    
                    status = 'PASS' if attempt.passed else 'FAIL' if attempt.is_completed else 'INCOMPLETE'
                    time_limit = quiz.time_limit if quiz.time_limit else 'No limit'
                    
                    writer.writerow([
                        user.name,
                        user.email,
                        quiz.title,
                        subject.name,
                        chapter.name,
                        f"{attempt.score:.1f}" if attempt.score else 'N/A',
                        status,
                        time_limit,
                        f"{quiz.pass_percentage}%",
                        attempt.date_taken.strftime('%d/%m/%Y %H:%M')
                    ])
                
                csv_data = output.getvalue()
                output.close()
                
                return {
                    'status': 'success',
                    'format': 'csv',
                    'data': csv_data,
                    'filename': f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            
            elif format == 'json':
                # Create JSON data
                report_data = []
                for attempt in all_attempts:
                    quiz = attempt.quiz
                    chapter = quiz.chapter
                    subject = chapter.subject
                    user = User.query.get(attempt.user_id)
                    
                    report_data.append({
                        'user_name': user.name,
                        'user_email': user.email,
                        'quiz_title': quiz.title,
                        'subject': subject.name,
                        'chapter': chapter.name,
                        'score': attempt.score,
                        'status': 'PASS' if attempt.passed else 'FAIL' if attempt.is_completed else 'INCOMPLETE',
                        'time_limit': quiz.time_limit,
                        'pass_percentage': quiz.pass_percentage,
                        'date_taken': attempt.date_taken.isoformat()
                    })
                
                return {
                    'status': 'success',
                    'format': 'json',
                    'data': json.dumps(report_data, indent=2),
                    'filename': f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                }
            
            else:
                return {'status': 'error', 'message': 'Unsupported format'}
                
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def cleanup_incomplete_attempts_task(self):
    """Clean up incomplete quiz attempts older than 24 hours"""
    try:
        with app.app_context():
            # Find incomplete attempts older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            old_attempts = QuizAttempt.query.filter(
                QuizAttempt.is_completed == False,
                QuizAttempt.date_taken < cutoff_time
            ).all()
            
            count = len(old_attempts)
            
            for attempt in old_attempts:
                db.session.delete(attempt)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'cleaned_attempts': count,
                'message': f'Cleaned up {count} incomplete attempts'
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(bind=True)
def update_quiz_statistics_task(self):
    """Update cached quiz statistics"""
    try:
        with app.app_context():
            from cache import cache
            
            # Get all quizzes
            quizzes = Quiz.query.all()
            
            stats = {}
            for quiz in quizzes:
                attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
                completed_attempts = [a for a in attempts if a.is_completed]
                
                if completed_attempts:
                    avg_score = sum(a.score for a in completed_attempts) / len(completed_attempts)
                    pass_rate = sum(1 for a in completed_attempts if a.passed) / len(completed_attempts) * 100
                    total_attempts = len(completed_attempts)
                else:
                    avg_score = 0
                    pass_rate = 0
                    total_attempts = 0
                
                stats[quiz.id] = {
                    'avg_score': round(avg_score, 2),
                    'pass_rate': round(pass_rate, 2),
                    'total_attempts': total_attempts,
                    'last_updated': datetime.utcnow().isoformat()
                }
            
            # Cache the statistics for 1 hour
            cache.set('quiz_statistics', stats, timeout=3600)
            
            return {
                'status': 'success',
                'updated_quizzes': len(quizzes),
                'message': f'Updated statistics for {len(quizzes)} quizzes'
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# Scheduled tasks
@celery.task
def send_scheduled_reminders():
    """Send automatic reminders for quizzes starting in 1 hour"""
    try:
        with app.app_context():
            now = datetime.utcnow()
            one_hour_from_now = now + timedelta(hours=1)
            
            # Find quizzes starting in the next hour
            upcoming_quizzes = Quiz.query.filter(
                Quiz.is_scheduled == True,
                Quiz.start_datetime >= now,
                Quiz.start_datetime <= one_hour_from_now
            ).all()
            
            for quiz in upcoming_quizzes:
                users = User.query.all()
                user_ids = [user.id for user in users if not user.is_admin]
                
                # Send reminder as background task
                send_quiz_reminder_task.delay(quiz.id, user_ids)
            
            return {
                'status': 'success',
                'quizzes_processed': len(upcoming_quizzes),
                'message': f'Processed {len(upcoming_quizzes)} quizzes for reminders'
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task
def send_monthly_reports():
    """Send monthly reports automatically on the first day of each month"""
    try:
        with app.app_context():
            now = datetime.utcnow()
            
            # Only send on the first day of the month
            if now.day == 1:
                users = User.query.filter_by(is_admin=False).all()
                user_ids = [user.id for user in users]
                
                # Send reports as background tasks
                for user_id in user_ids:
                    send_monthly_report_task.delay(user_id)
                
                return {
                    'status': 'success',
                    'users_processed': len(user_ids),
                    'message': f'Scheduled monthly reports for {len(user_ids)} users'
                }
            else:
                return {
                    'status': 'skipped',
                    'message': 'Not the first day of the month'
                }
                
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task
def daily_maintenance():
    """Daily maintenance tasks"""
    try:
        with app.app_context():
            # Clean up incomplete attempts
            cleanup_incomplete_attempts_task.delay()
            
            # Update quiz statistics
            update_quiz_statistics_task.delay()
            
            return {
                'status': 'success',
                'message': 'Daily maintenance tasks scheduled'
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)} 