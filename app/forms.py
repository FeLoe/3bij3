from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Nutzername', validators = [DataRequired()])
    password = PasswordField('Passwort', validators = [DataRequired()])
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Bitte nutzen Sie einen anderen Nutzernamen.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Bitte nutzen Sie eine andere Email Adresse')

class MultiCheckboxField(SelectMultipleField):
    option_widget = widgets.CheckboxInput()
    widget = widgets.ListWidget(prefix_label = False)

class ChecklisteForm(FlaskForm):
    list_of_files = ['Politik', 'Wirtschaft', 'Sport']
    files = [(x, x) for x in list_of_files]
    example = MultiCheckboxField('Label', choices=files)
    submit = SubmitField('Ändern')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Passwort', validators= [DataRequired()])
    password2 = PasswordField('Wiederhole Passwort', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Zurücksetzung Passwort anfordern')
