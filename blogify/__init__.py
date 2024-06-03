import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail                 # send mail in case of password reset

app = Flask(__name__)

# crsf key for protection against online attacks
app.config['SECRET_KEY'] = '7c4fb322e610bcbe62d664c0cc1fb7f0'
# set path for database, NOTE: /// -> indicates start point i.e, relative path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# set up SMTP server 
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# set user and pass
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

db = SQLAlchemy(app)

# for encrypting passwords
bcrypt = Bcrypt(app)    

# login manager 
login_manager = LoginManager(app)
login_manager.login_view = "login"                   # pass the function name for login route 
login_manager.login_message_category = "danger"      # set the flash message theme

# importing here to avoid circular importing issues
from blogify import routes
