from flask_mail import Message, Mail 
from flask import current_app
import os
mail = Mail()

def send_email(to, subject, template):
    msg = Message(
        subject, 
        recipients=[to],
        html=template,
        sender=os.getenv("MAIL_USERNAME")
    )
    mail.send(msg)