from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import os
import csv
import io
from models import db, User, Subject, Chapter, Quiz, Question, Option, QuizAttempt, QuizResponse
from forms import LoginForm, RegistrationForm, SubjectForm, ChapterForm, QuizForm, QuestionForm, OptionForm
from flask_mail import Mail, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Email configuration
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
# app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
# app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')

# Enable SQLite foreign key support
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Initialize database
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def send_quiz_notification(quiz, users):
    """Send email notification to users about a scheduled quiz"""
    try:
        subject = f"Quiz Scheduled: {quiz.title}"
        
        # Format the quiz details
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
        
        # Send to all users (except admins)
        user_count = 0
        for user in users:
            if not user.is_admin:
                user_count += 1
                msg = Message(
                    subject=subject,
                    recipients=[user.email],
                    body=body
                )
                mail.send(msg)
                print(f"📧 Email sent to {user.email}: {subject}")
                
        print(f"✅ Successfully sent {user_count} quiz notifications")
        return True
    except Exception as e:
        print(f"❌ Error sending email notification: {e}")
        return False

def send_quiz_reminder(quiz, users):
    """Send reminder email 1 hour before quiz starts"""
    try:
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
        
        user_count = 0
        for user in users:
            if not user.is_admin:
                user_count += 1
                msg = Message(
                    subject=subject,
                    recipients=[user.email],
                    body=body
                )
                mail.send(msg)
                print(f"📧 Reminder sent to {user.email}: {subject}")
                
        print(f"✅ Successfully sent {user_count} reminder emails")
        return True
    except Exception as e:
        print(f"❌ Error sending reminder email: {e}")
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Create database tables and initial data
with app.app_context():
    # Create all tables in PostgreSQL
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
    
    # Create admin user if not exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(name='Admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    # Auto-generate demo data if no subjects exist
    if Subject.query.count() == 0:
        from utils import create_demo_data
        try:
            create_demo_data()
            print("Demo data generated automatically!")
        except Exception as e:
            print(f"Error generating demo data: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('user_dashboard'))

# User routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    recent_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.date_taken.desc()).limit(5).all()
    # Only show available quizzes
    available_quizzes = [quiz for quiz in Quiz.query.all() if quiz.is_available and quiz.registration_open]
    return render_template('user/dashboard.html', recent_attempts=recent_attempts, available_quizzes=available_quizzes)

@app.route('/user/quizzes')
@login_required
def quiz_list():
    subjects = Subject.query.all()
    # Filter quizzes to only show available ones
    for subject in subjects:
        for chapter in subject.chapters:
            chapter.available_quizzes = [quiz for quiz in chapter.quizzes if quiz.is_available and quiz.registration_open]
    return render_template('user/quiz_list.html', subjects=subjects)

@app.route('/user/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    if current_user.is_admin:
        flash('Admins cannot attempt quizzes.', 'danger')
        return redirect(url_for('user_dashboard'))
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz is available based on schedule
    if not quiz.is_available:
        if quiz.is_scheduled:
            if quiz.time_until_start:
                days = quiz.time_until_start.days
                hours = quiz.time_until_start.seconds // 3600
                minutes = (quiz.time_until_start.seconds % 3600) // 60
                flash(f'This quiz is scheduled to start in {days} days, {hours} hours, {minutes} minutes.', 'warning')
            else:
                flash('This quiz has ended.', 'warning')
        else:
            flash('This quiz is not available.', 'warning')
        return redirect(url_for('quiz_list'))
    
    # Check if registration is still open
    if not quiz.registration_open:
        flash('Registration for this quiz has closed.', 'warning')
        return redirect(url_for('quiz_list'))
    
    # Check if user has already completed this quiz
    previous_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        is_completed=True
    ).first()
    
    if previous_attempt:
        flash('You have already completed this quiz. You cannot retake it.', 'warning')
        return redirect(url_for('quiz_results', attempt_id=previous_attempt.id))
    
    # Check if quiz has questions
    if not quiz.questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('quiz_list'))
    
    # Check if there's an incomplete attempt
    incomplete_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        is_completed=False
    ).first()
    
    if incomplete_attempt:
        # Convert incomplete attempt to completed with current responses
        incomplete_attempt.is_completed = True
        incomplete_attempt.score = 0  # Default score for abandoned attempts
        db.session.commit()
        flash('You previously left an attempt incomplete. It has been recorded as a submission.', 'warning')
    
    # Show the quiz info page with "Start Quiz" button
    return render_template('user/take_quiz.html', quiz=quiz)

@app.route('/user/quiz/<int:quiz_id>/start')
@login_required
def start_quiz_attempt(quiz_id):
    if current_user.is_admin:
        flash('Admins cannot attempt quizzes.', 'danger')
        return redirect(url_for('user_dashboard'))
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz is available based on schedule
    if not quiz.is_available:
        if quiz.is_scheduled:
            if quiz.time_until_start:
                days = quiz.time_until_start.days
                hours = quiz.time_until_start.seconds // 3600
                minutes = (quiz.time_until_start.seconds % 3600) // 60
                flash(f'This quiz is scheduled to start in {days} days, {hours} hours, {minutes} minutes.', 'warning')
            else:
                flash('This quiz has ended.', 'warning')
        else:
            flash('This quiz is not available.', 'warning')
        return redirect(url_for('quiz_list'))
    
    # Check if registration is still open
    if not quiz.registration_open:
        flash('Registration for this quiz has closed.', 'warning')
        return redirect(url_for('quiz_list'))
    
    # Check if user has already completed this quiz
    previous_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        is_completed=True
    ).first()
    
    if previous_attempt:
        flash('You have already completed this quiz. You cannot retake it.', 'warning')
        return redirect(url_for('quiz_results', attempt_id=previous_attempt.id))
    
    # Check for and remove any incomplete attempts
    incomplete_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        is_completed=False
    ).all()
    
    for old_attempt in incomplete_attempts:
        db.session.delete(old_attempt)
    
    db.session.commit()
    
    # Create a new quiz attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        date_taken=datetime.now(),
        is_completed=False
    )
    db.session.add(attempt)
    db.session.commit()
    
    session['current_attempt_id'] = attempt.id
    session['time_remaining'] = quiz.time_limit * 60 if quiz.time_limit else None
    
    return render_template('user/attempt_quiz.html', quiz=quiz, attempt=attempt)

@app.route('/user/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    if current_user.is_admin:
        flash('Admins cannot attempt quizzes.', 'danger')
        return redirect(url_for('user_dashboard'))
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt_id = session.get('current_attempt_id')
    
    if not attempt_id:
        flash('Invalid quiz attempt.', 'danger')
        return redirect(url_for('quiz_list'))
    
    attempt = QuizAttempt.query.get(attempt_id)
    
    # Calculate score
    total_questions = len(quiz.questions)
    correct_answers = 0
    
    for question in quiz.questions:
        selected_option_id = request.form.get(f'question_{question.id}')
        if selected_option_id:
            selected_option = Option.query.get(int(selected_option_id))
            response = QuizResponse(
                attempt_id=attempt_id,
                question_id=question.id,
                option_id=selected_option.id
            )
            db.session.add(response)
            if selected_option.is_correct:
                correct_answers += 1
    
    # Update attempt
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    attempt.score = score_percentage
    attempt.is_completed = True
    db.session.commit()
    
    # Clear session data
    session.pop('current_attempt_id', None)
    session.pop('time_remaining', None)
    
    flash(f'Quiz submitted! Your score: {score_percentage:.1f}%', 'success')
    return redirect(url_for('quiz_results', attempt_id=attempt_id))

@app.route('/user/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Ensure the user can only see their own results
    if attempt.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view these results.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    return render_template('user/results.html', attempt=attempt)

@app.route('/user/history')
@login_required
def quiz_history():
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.date_taken.desc()).all()
    return render_template('user/history.html', attempts=attempts)

@app.route('/user/history/download')
@login_required
def download_user_history():
    if current_user.is_admin:
        flash('Admins cannot download user history.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Get user's quiz attempts
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.date_taken.desc()).all()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Quiz Title', 'Subject', 'Chapter', 'Score (%)', 'Status', 'Time Limit (min)', 'Pass Percentage', 'Date/Time'])
    
    # Write data
    for attempt in attempts:
        quiz = attempt.quiz
        chapter = quiz.chapter
        subject = chapter.subject
        
        status = 'PASS' if attempt.passed else 'FAIL' if attempt.is_completed else 'INCOMPLETE'
        time_limit = quiz.time_limit if quiz.time_limit else 'No limit'
        
        writer.writerow([
            quiz.title,
            subject.name,
            chapter.name,
            f"{attempt.score:.1f}" if attempt.score else 'N/A',
            status,
            time_limit,
            f"{quiz.pass_percentage}%",
            attempt.date_taken.strftime('%d/%m/%Y %H:%M')
        ])
    
    # Prepare file for download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'quiz_history_{current_user.name}_{datetime.now().strftime("%Y%m%d")}.csv'
    )

def send_monthly_report(user):
    """Send monthly performance report to user"""
    try:
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
            return False  # No attempts this month
        
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
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=body
        )
        mail.send(msg)
        print(f"📧 Monthly report sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending monthly report to {user.email}: {e}")
        return False

@app.route('/admin/send-monthly-reports')
@login_required
@admin_required
def send_monthly_reports():
    """Manually trigger monthly reports for all users"""
    users = User.query.filter_by(is_admin=False).all()
    success_count = 0
    
    for user in users:
        if send_monthly_report(user):
            success_count += 1
    
    flash(f'Monthly reports sent to {success_count} users successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/user/analysis')
@login_required
def user_analysis():
    # Get all completed attempts for the current user
    attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(QuizAttempt.date_taken.desc()).all()
    
    # Calculate basic stats
    total_quizzes = len(attempts)
    avg_score = sum(attempt.score for attempt in attempts) / total_quizzes if total_quizzes > 0 else 0
    highest_score = max((attempt.score for attempt in attempts), default=0)
    
    # Calculate total time spent (in minutes)
    total_time = sum(
        attempt.quiz.time_limit 
        for attempt in attempts 
        if attempt.quiz.time_limit is not None
    )
    
    # Performance over time data
    dates = [attempt.date_taken.strftime('%Y-%m-%d') for attempt in attempts]
    scores = [attempt.score for attempt in attempts]
    
    # Subject performance data
    subject_data = {}
    for attempt in attempts:
        subject_name = attempt.quiz.chapter.subject.name
        if subject_name not in subject_data:
            subject_data[subject_name] = {
                'scores': [],
                'time_spent': 0
            }
        subject_data[subject_name]['scores'].append(attempt.score)
        if attempt.quiz.time_limit:
            subject_data[subject_name]['time_spent'] += attempt.quiz.time_limit
    
    subject_names = list(subject_data.keys())
    subject_scores = [
        sum(data['scores']) / len(data['scores']) 
        for data in subject_data.values()
    ]
    subject_times = [
        data['time_spent'] 
        for data in subject_data.values()
    ]
    
    # Recent attempts for the table
    recent_attempts = []
    for attempt in attempts[:10]:  # Last 10 attempts
        recent_attempts.append({
            'quiz_name': attempt.quiz.title,
            'subject': attempt.quiz.chapter.subject.name,
            'score': attempt.score,
            'time_taken': f"{attempt.quiz.time_limit} min" if attempt.quiz.time_limit else "No limit",
            'date': attempt.date_taken
        })
    
    return render_template(
        'user_analysis.html',
        total_quizzes=total_quizzes,
        avg_score=round(avg_score, 1),
        highest_score=round(highest_score, 1),
        total_time=f"{total_time} min",
        dates=dates,
        scores=scores,
        subject_names=subject_names,
        subject_scores=subject_scores,
        subject_times=subject_times,
        recent_attempts=recent_attempts
    )

# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users_count = User.query.count()
    quizzes_count = Quiz.query.count()
    subjects_count = Subject.query.count()
    attempts_count = QuizAttempt.query.count()
    
    return render_template('admin/dashboard.html', 
                          users_count=users_count, 
                          quizzes_count=quizzes_count,
                          subjects_count=subjects_count,
                          attempts_count=attempts_count)

# Admin - User Management
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/toggle/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # Prevent admin from removing their own admin status
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"Admin status for {user.name} has been {'granted' if user.is_admin else 'revoked'}.", 'success')
    else:
        flash("You cannot change your own admin status.", 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # Prevent admin from deleting themselves
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.name} has been deleted.", 'success')
    else:
        flash("You cannot delete your own account while logged in.", 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/download-all')
@login_required
@admin_required
def download_all_users_performance():
    """Download performance reports for all users"""
    users = User.query.filter_by(is_admin=False).all()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['User Name', 'User Email', 'Quiz Title', 'Subject', 'Chapter', 'Score (%)', 'Status', 'Time Limit (min)', 'Pass Percentage', 'Date/Time'])
    
    # Write data for all users
    for user in users:
        attempts = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.date_taken.desc()).all()
        
        for attempt in attempts:
            quiz = attempt.quiz
            chapter = quiz.chapter
            subject = chapter.subject
            
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
    
    # Prepare file for download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'all_users_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

# Admin - Subject Management
@app.route('/admin/subjects')
@login_required
@admin_required
def admin_subjects():
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data, description=form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
        return redirect(url_for('admin_subjects'))
    return render_template('admin/subject_form.html', form=form, title='Add Subject')

@app.route('/admin/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin_subjects'))
    return render_template('admin/subject_form.html', form=form, title='Edit Subject')

@app.route('/admin/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('admin_subjects'))

# Admin - Chapter Management
@app.route('/admin/chapters')
@login_required
@admin_required
def admin_chapters():
    chapters = Chapter.query.all()
    return render_template('admin/chapters.html', chapters=chapters)

@app.route('/admin/chapters/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_chapter():
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        chapter = Chapter(
            name=form.name.data,
            description=form.description.data,
            subject_id=form.subject_id.data
        )
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter added successfully!', 'success')
        return redirect(url_for('admin_chapters'))
    return render_template('admin/chapter_form.html', form=form, title='Add Chapter')

@app.route('/admin/chapters/edit/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data
        chapter.subject_id = form.subject_id.data
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('admin_chapters'))
    return render_template('admin/chapter_form.html', form=form, title='Edit Chapter')

@app.route('/admin/chapters/delete/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('admin_chapters'))

# Admin - Quiz Management
@app.route('/admin/quizzes')
@login_required
@admin_required
def admin_quizzes():
    # Get all quizzes with their relationships pre-loaded
    quizzes = Quiz.query.options(
        db.joinedload(Quiz.chapter).joinedload(Chapter.subject),
        db.joinedload(Quiz.questions)
    ).all()
    return render_template('admin/quizzes.html', quizzes=quizzes)

@app.route('/admin/quizzes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_quiz():
    form = QuizForm()
    form.chapter_id.choices = [(c.id, f"{c.name} ({c.subject.name})") for c in Chapter.query.all()]
    if form.validate_on_submit():
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            chapter_id=form.chapter_id.data,
            time_limit=form.time_limit.data,
            pass_percentage=form.pass_percentage.data,
            is_scheduled=form.is_scheduled.data,
            start_datetime=form.start_datetime.data if form.is_scheduled.data else None,
            end_datetime=form.end_datetime.data if form.is_scheduled.data else None
        )
        db.session.add(quiz)
        db.session.commit()
        
        # Send email notification if quiz is scheduled
        if quiz.is_scheduled and quiz.start_datetime:
            users = User.query.all()
            if send_quiz_notification(quiz, users):
                flash('Quiz added successfully and notifications sent!', 'success')
            else:
                flash('Quiz added successfully but notification sending failed.', 'warning')
        else:
            flash('Quiz added successfully!', 'success')
            
        return redirect(url_for('admin_quizzes'))
    return render_template('admin/quiz_form.html', form=form, title='Add Quiz')

@app.route('/admin/quizzes/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizForm(obj=quiz)
    form.chapter_id.choices = [(c.id, f"{c.name} ({c.subject.name})") for c in Chapter.query.all()]
    
    # Store original scheduling state
    was_scheduled = quiz.is_scheduled
    
    if form.validate_on_submit():
        quiz.title = form.title.data
        quiz.description = form.description.data
        quiz.chapter_id = form.chapter_id.data
        quiz.time_limit = form.time_limit.data
        quiz.pass_percentage = form.pass_percentage.data
        quiz.is_scheduled = form.is_scheduled.data
        quiz.start_datetime = form.start_datetime.data if form.is_scheduled.data else None
        quiz.end_datetime = form.end_datetime.data if form.is_scheduled.data else None
        db.session.commit()
        
        # Send email notification if quiz is newly scheduled or scheduling was updated
        if quiz.is_scheduled and quiz.start_datetime:
            users = User.query.all()
            if not was_scheduled or (was_scheduled and quiz.start_datetime != form.start_datetime.data):
                if send_quiz_notification(quiz, users):
                    flash('Quiz updated successfully and notifications sent!', 'success')
                else:
                    flash('Quiz updated successfully but notification sending failed.', 'warning')
            else:
                flash('Quiz updated successfully!', 'success')
        else:
            flash('Quiz updated successfully!', 'success')
            
        return redirect(url_for('admin_quizzes'))
    return render_template('admin/quiz_form.html', form=form, title='Edit Quiz')

@app.route('/admin/quizzes/delete/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('admin_quizzes'))

# Admin - Question Management
@app.route('/admin/quizzes/<int:quiz_id>/questions')
@login_required
@admin_required
def admin_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('admin/questions.html', quiz=quiz)

@app.route('/admin/quizzes/<int:quiz_id>/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            quiz_id=quiz_id,
            text=form.text.data,
            points=form.points.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully! Now add options for this question.', 'success')
        return redirect(url_for('add_options', question_id=question.id))
    return render_template('admin/question_form.html', form=form, quiz=quiz, title='Add Question')

@app.route('/admin/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question)
    if form.validate_on_submit():
        question.text = form.text.data
        question.points = form.points.data
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_questions', quiz_id=question.quiz_id))
    return render_template('admin/question_form.html', form=form, quiz=question.quiz, title='Edit Question')

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_questions', quiz_id=quiz_id))

# Admin - Option Management
@app.route('/admin/questions/<int:question_id>/options')
@login_required
@admin_required
def admin_options(question_id):
    question = Question.query.get_or_404(question_id)
    return render_template('admin/options.html', question=question)

@app.route('/admin/questions/<int:question_id>/options/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_options(question_id):
    question = Question.query.get_or_404(question_id)
    form = OptionForm()
    if form.validate_on_submit():
        option = Option(
            question_id=question_id,
            text=form.text.data,
            is_correct=form.is_correct.data
        )
        db.session.add(option)
        db.session.commit()
        flash('Option added successfully!', 'success')
        return redirect(url_for('admin_options', question_id=question_id))
    return render_template('admin/option_form.html', form=form, question=question, title='Add Option')

@app.route('/admin/options/<int:option_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_option(option_id):
    option = Option.query.get_or_404(option_id)
    form = OptionForm(obj=option)
    if form.validate_on_submit():
        option.text = form.text.data
        option.is_correct = form.is_correct.data
        db.session.commit()
        flash('Option updated successfully!', 'success')
        return redirect(url_for('admin_options', question_id=option.question_id))
    return render_template('admin/option_form.html', form=form, question=option.question, title='Edit Option')

@app.route('/admin/options/<int:option_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_option(option_id):
    option = Option.query.get_or_404(option_id)
    question_id = option.question_id
    db.session.delete(option)
    db.session.commit()
    flash('Option deleted successfully!', 'success')
    return redirect(url_for('admin_options', question_id=question_id))

@app.route('/admin/attempts')
@login_required
@admin_required
def admin_attempts():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    subject_id = request.args.get('subject_id', type=int)
    chapter_id = request.args.get('chapter_id', type=int)
    quiz_id = request.args.get('quiz_id', type=int)
    user_id = request.args.get('user_id', type=int)
    status = request.args.get('status')
    
    # Base query
    attempts_query = db.session.query(
        QuizAttempt, Quiz, Subject, Chapter, User
    ).join(
        Quiz, QuizAttempt.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).join(
        User, QuizAttempt.user_id == User.id
    ).order_by(QuizAttempt.date_taken.desc())
    
    # Apply filters
    if subject_id:
        attempts_query = attempts_query.filter(Subject.id == subject_id)
    if chapter_id:
        attempts_query = attempts_query.filter(Chapter.id == chapter_id)
    if quiz_id:
        attempts_query = attempts_query.filter(Quiz.id == quiz_id)
    if user_id:
        attempts_query = attempts_query.filter(User.id == user_id)
    if status:
        if status == 'pass':
            attempts_query = attempts_query.filter(
                QuizAttempt.score >= Quiz.pass_score
            )
        elif status == 'fail':
            attempts_query = attempts_query.filter(
                QuizAttempt.score < Quiz.pass_score
            )
    
    attempts = attempts_query.all()
    
    # Calculate pass/fail status for each attempt
    attempt_results = []
    for attempt, quiz, subject, chapter, user in attempts:
        total_questions = len(quiz.questions)
        # Use the attempt.score directly as it's already a percentage
        passed = attempt.score >= quiz.pass_percentage if attempt.score is not None else False
        attempt_results.append({
            'attempt': attempt,
            'quiz': quiz,
            'subject': subject,
            'chapter': chapter,
            'user': user,
            'percentage': attempt.score if attempt.score is not None else 0,
            'passed': passed
        })
    
    # Get filter options
    subjects = Subject.query.order_by(Subject.name).all()
    chapters = Chapter.query.order_by(Chapter.name).all()
    quizzes = Quiz.query.order_by(Quiz.title).all()
    users = User.query.order_by(User.name).all()
    
    return render_template(
        'admin/attempts.html',
        attempt_results=attempt_results,
        subjects=subjects,
        chapters=chapters,
        quizzes=quizzes,
        users=users,
        subject_id=subject_id,
        chapter_id=chapter_id,
        quiz_id=quiz_id,
        user_id=user_id,
        status=status
    )

@app.route('/admin/attempts/download')
@login_required
@admin_required
def download_admin_performance():
    # Get all quiz attempts with related data
    attempts_query = db.session.query(
        QuizAttempt, Quiz, Subject, Chapter, User
    ).join(
        Quiz, QuizAttempt.quiz_id == Quiz.id
    ).join(
        Chapter, Quiz.chapter_id == Chapter.id
    ).join(
        Subject, Chapter.subject_id == Subject.id
    ).join(
        User, QuizAttempt.user_id == User.id
    ).order_by(User.name, QuizAttempt.date_taken.desc())
    
    attempts = attempts_query.all()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['User Name', 'User Email', 'Quiz Title', 'Subject', 'Chapter', 'Score (%)', 'Status', 'Time Limit (min)', 'Pass Percentage', 'Questions Count'])
    
    # Write data
    for attempt, quiz, subject, chapter, user in attempts:
        status = 'PASS' if attempt.score >= quiz.pass_percentage else 'FAIL' if attempt.is_completed else 'INCOMPLETE'
        time_limit = quiz.time_limit if quiz.time_limit else 'No limit'
        questions_count = len(quiz.questions)
        
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
            questions_count
        ])
    
    # Prepare file for download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'user_performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/result/<int:attempt_id>')
@login_required
def view_result(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Check if the user is the owner of the attempt or an admin
    if attempt.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this result.', 'danger')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get(attempt.quiz_id)
    user = User.query.get(attempt.user_id)
    
    # Get the detailed responses (assuming you have a model for this)
    responses = QuizResponse.query.filter_by(attempt_id=attempt.id).all()
    
    return render_template(
        'result.html',
        attempt=attempt,
        quiz=quiz,
        user=user,
        responses=responses
    )

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = {'quizzes': [], 'subjects': [], 'users': []}
    if query:
        # Search quizzes by title or description
        results['quizzes'] = Quiz.query.filter(
            (Quiz.title.ilike(f'%{query}%')) | (Quiz.description.ilike(f'%{query}%'))
        ).all()
        # Search subjects by name or description
        results['subjects'] = Subject.query.filter(
            (Subject.name.ilike(f'%{query}%')) | (Subject.description.ilike(f'%{query}%'))
        ).all()
        # Search users by name or email (admin only)
        if current_user.is_authenticated and current_user.is_admin:
            results['users'] = User.query.filter(
                (User.name.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
            ).all()
    return render_template('search_results.html', query=query, results=results)

# Demo data is now generated automatically when the database is empty

@app.route('/admin/send-reminders/<int:quiz_id>')
@login_required
@admin_required
def send_quiz_reminders(quiz_id):
    """Manually send reminder emails for a specific quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_scheduled or not quiz.start_datetime:
        flash('This quiz is not scheduled.', 'warning')
        return redirect(url_for('admin_quizzes'))
    
    users = User.query.all()
    if send_quiz_reminder(quiz, users):
        flash(f'Reminder emails sent for quiz: {quiz.title}', 'success')
    else:
        flash('Failed to send reminder emails.', 'error')
    
    return redirect(url_for('admin_quizzes'))

def send_scheduled_reminders():
    """Send automatic reminders for quizzes starting in 1 hour"""
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
        send_quiz_reminder(quiz, users)
        print(f"Sent reminder for quiz: {quiz.title}")

def send_automatic_monthly_reports():
    """Send monthly reports automatically on the first day of each month"""
    now = datetime.utcnow()
    
    # Only send on the first day of the month
    if now.day == 1:
        users = User.query.filter_by(is_admin=False).all()
        success_count = 0
        
        for user in users:
            if send_monthly_report(user):
                success_count += 1
        
        print(f"📧 Automatic monthly reports sent to {success_count} users")
        return success_count
    
    return 0

@app.route('/admin/users/<int:user_id>/download')
@login_required
@admin_required
def download_user_performance(user_id):
    """Download performance report for a specific user"""
    user = User.query.get_or_404(user_id)
    
    # Get all quiz attempts for this user
    attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(QuizAttempt.date_taken.desc()).all()
    
    # Create CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['User Name', 'User Email', 'Quiz Title', 'Subject', 'Chapter', 'Score (%)', 'Status', 'Time Limit (min)', 'Pass Percentage', 'Date/Time'])
    
    # Write data
    for attempt in attempts:
        quiz = attempt.quiz
        chapter = quiz.chapter
        subject = chapter.subject
        
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
    
    # Prepare file for download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'user_performance_{user.name}_{datetime.now().strftime("%Y%m%d")}.csv'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)