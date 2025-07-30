from datetime import datetime, timedelta
import random
import string
from models import db, User, Subject, Chapter, Quiz, Question, Option

def format_time(seconds):
    """Format seconds into MM:SS format"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def calculate_score(attempt):
    """Calculate score percentage for a quiz attempt"""
    total_questions = len(attempt.quiz.questions)
    if total_questions == 0:
        return 0
    
    correct_answers = 0
    for response in attempt.responses:
        if response.selected_option.is_correct:
            correct_answers += 1
    
    return (correct_answers / total_questions) * 100

def generate_random_password(length=10):
    """Generate a random password of specified length"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def create_demo_data():
    """Create demo data for testing"""
    # Create subjects
    math = Subject(name="Mathematics", description="Study of numbers, quantities, and shapes")
    science = Subject(name="Science", description="Study of the natural world through observation and experiment")
    history = Subject(name="History", description="Study of past events")
    
    db.session.add_all([math, science, history])
    db.session.commit()
    
    # Create chapters
    algebra = Chapter(name="Algebra", description="Study of mathematical symbols and rules", subject_id=math.id)
    geometry = Chapter(name="Geometry", description="Study of shapes and their properties", subject_id=math.id)
    
    physics = Chapter(name="Physics", description="Study of matter, energy, and their interactions", subject_id=science.id)
    biology = Chapter(name="Biology", description="Study of living organisms", subject_id=science.id)
    
    ancient = Chapter(name="Ancient History", description="History before the Middle Ages", subject_id=history.id)
    modern = Chapter(name="Modern History", description="History from the Renaissance to present", subject_id=history.id)
    
    db.session.add_all([algebra, geometry, physics, biology, ancient, modern])
    db.session.commit()
    
    # Create quizzes
    algebra_quiz = Quiz(
        title="Basic Algebra Quiz",
        description="Test your knowledge of basic algebraic concepts",
        chapter_id=algebra.id,
        time_limit=10,
        pass_percentage=60.0
    )
    
    physics_quiz = Quiz(
        title="Physics Fundamentals",
        description="Test your understanding of basic physics concepts",
        chapter_id=physics.id,
        time_limit=15,
        pass_percentage=70.0
    )
    
    ancient_quiz = Quiz(
        title="Ancient Civilizations",
        description="Test your knowledge of ancient civilizations",
        chapter_id=ancient.id,
        time_limit=None,
        pass_percentage=50.0
    )
    
    db.session.add_all([algebra_quiz, physics_quiz, ancient_quiz])
    db.session.commit()
    
    # Create questions and options for Algebra quiz
    q1 = Question(quiz_id=algebra_quiz.id, text="What is the value of x in the equation 2x + 5 = 15?", points=1)
    db.session.add(q1)
    db.session.commit()
    
    db.session.add_all([
        Option(question_id=q1.id, text="5", is_correct=True),
        Option(question_id=q1.id, text="7", is_correct=False),
        Option(question_id=q1.id, text="10", is_correct=False),
        Option(question_id=q1.id, text="3", is_correct=False)
    ])
    
    q2 = Question(quiz_id=algebra_quiz.id, text="Simplify: 3(2x - 4) + 5", points=1)
    db.session.add(q2)
    db.session.commit()
    
    db.session.add_all([
        Option(question_id=q2.id, text="6x - 7", is_correct=True),
        Option(question_id=q2.id, text="6x - 12", is_correct=False),
        Option(question_id=q2.id, text="6x - 17", is_correct=False),
        Option(question_id=q2.id, text="6x + 5", is_correct=False)
    ])
    
    # Create questions and options for Physics quiz
    q3 = Question(quiz_id=physics_quiz.id, text="What is Newton's First Law of Motion?", points=1)
    db.session.add(q3)
    db.session.commit()
    
    db.session.add_all([
        Option(question_id=q3.id, text="An object at rest stays at rest, and an object in motion stays in motion unless acted upon by an external force", is_correct=True),
        Option(question_id=q3.id, text="Force equals mass times acceleration", is_correct=False),
        Option(question_id=q3.id, text="For every action, there is an equal and opposite reaction", is_correct=False),
        Option(question_id=q3.id, text="Energy can neither be created nor destroyed", is_correct=False)
    ])
    
    # Create questions and options for Ancient History quiz
    q4 = Question(quiz_id=ancient_quiz.id, text="Which civilization built the Great Pyramids of Giza?", points=1)
    db.session.add(q4)
    db.session.commit()
    
    db.session.add_all([
        Option(question_id=q4.id, text="Ancient Egypt", is_correct=True),
        Option(question_id=q4.id, text="Ancient Greece", is_correct=False),
        Option(question_id=q4.id, text="Mesopotamia", is_correct=False),
        Option(question_id=q4.id, text="Roman Empire", is_correct=False)
    ])
    
    db.session.commit()
    print("Demo data created successfully!")