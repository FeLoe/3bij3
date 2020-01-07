'''
Provides functionality to send emails to users.
'''
from threading import Thread
from flask_mail import Message
from flask import render_template
from app import mail, app

def send_email(subject, sender, recipients, text_body, html_body):
    '''sends an email (generic)'''
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=_send_async_email, args=(app, msg)).start()

def send_password_reset_email(user, email):
    '''sends a password-reset mail'''
    token = user.get_reset_password_token()
    send_email('(3bij3) Wachtwoord opnieuw instellen',
               sender=app.config['ADMINS'][0],
               recipients=[email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_registration_confirmation(user, email):
    '''sends a confirmation mail after users register for the first time'''
    send_email('3bij3 registratie voltooid - activeer jouw account',
               sender=app.config['ADMINS'][0],
               recipients=[email],
               text_body=render_template('email/registration_confirmation.txt',
                                         user=user),
               html_body=render_template('email/registration_confirmation.html',
                                         user=user))
def _send_async_email(myapp, msg):
    with myapp.app_context():
        mail.send(msg)
