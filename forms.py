from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, IntegerField, FloatField, SelectField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Save')

class ChapterForm(FlaskForm):
    name = StringField('Chapter Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    time_limit = IntegerField('Time Limit (minutes)', validators=[Optional()])
    pass_percentage = FloatField('Pass Percentage', validators=[DataRequired(), NumberRange(min=0, max=100)], default=50.0)
    is_scheduled = BooleanField('Schedule this quiz')
    start_datetime = DateTimeField('Start Date & Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_datetime = DateTimeField('End Date & Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('Submit')

class QuestionForm(FlaskForm):
    text = TextAreaField('Question Text', validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField('Save')

class OptionForm(FlaskForm):
    text = TextAreaField('Option Text', validators=[DataRequired()])
    is_correct = BooleanField('Correct Answer')
    submit = SubmitField('Save')