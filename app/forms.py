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
    list_of_files = ['politiek', 'economie', 'sport']
    files = [(x, x) for x in list_of_files]
    example = MultiCheckboxField('Label', choices=files)
    submit = SubmitField('Wijzigen')

    def validate(self):                                                         
        rv = FlaskForm.validate(self)                                           
        if not rv:                                                              
            return False                                                                                                       
        if len(self.example.data) > 2:                                          
            self.example.errors.append('Let op! U kunt maximaal drie categoriÃ«n kiezen.')    
            return False                                                        
        return True 

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Verzoek wachtwoord reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Wachtwoord', validators= [DataRequired()])
    password2 = PasswordField('Herhaal wachtwoord', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Verzoek wachtwoord reset')


class SurveyForm(FlaskForm):
    gender = RadioField('Wat is uw geslacht?',
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Ik geef liever geen antwoord')],validators=[DataRequired()], default=None)
    age = IntegerField('In welk jaar bent u geboren?', validators=[DataRequired(), InputRequired(), Length(min = 4, max = 4, message = "Geef een geldig geboortejaar op"), NumberRange(min = 1918, max = 2002, message = "Geef een geldig geboortejaar op")])
    education = RadioField('Wat is uw hoogst behaalde opleidingsniveau?',
        choices=[('1', 'Geen onderwijs / basisonderwijs / lagere school'),
            ('2', 'LBO / VBO / VMBO (kader- en beroepsgerichte leerweg)'), ('3', 'MAVO / eerste 3 jaar HAVO en VWO / VMBO (theoretische en gemengde leerweg)'),('4', 'MBO'), ('Grad', 'HAVO en VWO bovenbouw / WO-propedeuse'),('5', 'HBO / WO-bachelor of kandidaats '), ('6', 'WO-doctoraal of master')],validators=[DataRequired()])
    submit = SubmitField('Afzenden')

class rating(FlaskForm):
    rating = TextAreaField()
