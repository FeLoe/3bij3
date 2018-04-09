from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, RadioField, SelectField,  SubmitField, SelectMultipleField, TextAreaField, widgets, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, InputRequired, Length, NumberRange
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators = [DataRequired()])
    password = PasswordField('Wachtwoord', validators = [DataRequired()])
    remember_me = BooleanField('Ingelogd blijven')
    submit = SubmitField('Inloggen')

class RegistrationForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Wachtwoord', validators = [DataRequired()])
    password2 = PasswordField('Herhaal wachtwoord', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registreren')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Dit gebruikersnaam is al in gebruik, gebruik alstublieft een ander gebruikersnaam.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Dit email adres is al in gebruik, gebruik alstublieft een ander email adres.')

class MultiCheckboxField(SelectMultipleField):
    option_widget = widgets.CheckboxInput()
    widget = widgets.ListWidget(prefix_label = False)

class ChecklisteForm(FlaskForm):
    list_of_files = ['Binnenland', 'Buitenland', 'Economie', 'Milieu', 'Wetenschap en technologie', 'Immigratie en integratie', 'Justitie en Criminaliteit', 'Sport', 'Kunst, cultuur en entertainment', 'Anders/Diversen']
    files = [(x, x) for x in list_of_files]
    example = MultiCheckboxField('Label', choices=files)
    submit = SubmitField('Wijzigen')

    def validate(self):                                                         
        rv = FlaskForm.validate(self)                                           
        if not rv:                                                              
            return False                                                                                                       
        if len(self.example.data) > 2:                                          
            self.example.errors.append('Let op! U kunt maximaal drie opties kiezen.')    
            return False                                                        
        return True 

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Verzoek wachtwoord reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Wachtwoord', validators= [DataRequired()])
    password2 = PasswordField('Herhaal wachtwoord', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Verzoek wachtwoord reset')


class rating(FlaskForm):
    rating = TextAreaField()

class ContactForm(FlaskForm):
    lead = TextAreaField('Onderwerp:', validators = [DataRequired()])
    message = TextAreaField('Uw bericht:', validators = [DataRequired()])
    submit = SubmitField('Afzenden')

class ReportForm(FlaskForm):
    lead = TextAreaField('Onderwerp:', validators = [DataRequired()])
    message = TextAreaField('Wat voor soort problemen zijn er met het artikel?', validators = [DataRequired()])
    submit = SubmitField('Afzenden')
