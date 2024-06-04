from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo
from blogify.models import User
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField(
        label='username',
        validators=[DataRequired(), Length(min=5, max=20)]
    )

    email = EmailField(
        label='email',
        validators=[DataRequired()]
    )

    password = PasswordField(
        label='password',
        validators=[DataRequired(), Length(min=8)]
    )

    confirm_password = PasswordField(
        label='confirm password',
        validators=[DataRequired(), EqualTo('password')]
    )

    submit = SubmitField(label='Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already exists. Try a different one.")

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError("An account with this email already exists. Please user another email.")


class LoginForm(FlaskForm):
    email = EmailField(
        label='email',
        validators=[DataRequired()]
    )

    password = PasswordField(
        label='password',
        validators=[DataRequired(), Length(min=8)]
    )

    remember = BooleanField(label='Remember Me')
    submit = SubmitField(label='Login')


class UpdateAccountForm(FlaskForm):
    username = StringField(
        label='username',
        validators=[DataRequired(), Length(min=5, max=20)]
    )

    email = EmailField(
        label='email',
        validators=[DataRequired()]
    )

    picture = FileField(
        'Update profile pic',
        validators=[FileAllowed(['jpg', 'png', 'jpeg', 'pdf'])]
    )

    submit = SubmitField(label='Update')

    def validate_username(self, username):
        if current_user.username != username.data:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("Username already exists. Try a different one.")

    def validate_email(self, email):
        if current_user.email != email.data:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError("An account with this email already exists. Please user another email.")


class PostForm(FlaskForm):
    title = StringField(
        label="Title",
        validators=[DataRequired()]
    )

    content = TextAreaField(
        label="Content",
        validators=[DataRequired()]
    )

    submit = SubmitField(
        label="Post"
    )


class RequestResetForm(FlaskForm):
    email = EmailField(
        label='email',
        validators=[DataRequired()]
    )

    submit = SubmitField(
        label="Request Password Reset"
    )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("This email is not registered. You must register First.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        label='password',
        validators=[DataRequired(), Length(min=8)]
    )

    confirm_password = PasswordField(
        label='confirm password',
        validators=[DataRequired(), EqualTo('password')]
    )

    submit = SubmitField(
        label="Reset Password"
    )
