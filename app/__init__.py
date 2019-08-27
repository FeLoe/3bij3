from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_moment import Moment
import gensim
import pickle
import joblib
from gensim.similarities import SoftCosineSimilarity

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
bootstrap = Bootstrap(app)
mail = Mail(app)
moment = Moment(app)

#Different parameters that can be specified depending on the recommenders that are used.
#LDA_model and LDA_dict are for using the LDA recommender
# dictionary, index and article_ids are used if past_behavior (SoftCosine) recommender is used

try:
    lda_model = gensim.models.LdaModel.load("put path to model here")
except:
    lda_model = None
try:    
    lda_dict = gensim.corpora.Dictionary.load("/put path to dict here")
except:
    lda_dict = None
try:
    dictionary = gensim.corpora.Dictionary.load("put path to dict here")
except:
    dictionary = None
try:
    index = SoftCosineSimilarity.load('put path to index here')
except:
    index = None
try:
    article_ids = pickle.load(open('put path to article ids here', 'rb'))
except:
    article_ids = None

login.login_view = 'login'
if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost = (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr = 'no-reply@' + app.config['MAIL_SERVER'],
            toaddrs = app.config['ADMINS'], subject= '3bij3 Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/3bij3.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('3bij3 startup')
try:
    mysql_database = app.config['MYSQL_DATABASE']
    mysql_user = app.config['MYSQL_USER']
    mysql_password = app.config['MYSQL_PASSWORD']
except:
    mysql_database = None
    mysql_user = None
    mysql_password = None
    
from app import routes, models, errors, recommender, processing
