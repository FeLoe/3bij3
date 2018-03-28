from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from time import time
import jwt
from app import app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index=True, unique = True)
    password_hash = db.Column(db.String(128))
    group = db.Column(db.Integer)
    first_login = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    categories = db.relationship('Category', backref = 'user', lazy = 'dynamic')
    displayed_news = db.relationship('News', backref = 'user', lazy = 'dynamic')
    selected_news = db.relationship('News_sel', backref = 'user', lazy = 'dynamic')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp':time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms = ['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key =True)
    Binnenland = db.Column(db.Integer)
    Buitenland = db.Column(db.Integer)
    Economie = db.Column(db.Integer)
    Milieu=db.Column(db.Integer)
    Wetenschap=db.Column(db.Integer)
    Immigratie=db.Column(db.Integer)
    Justitie=db.Column(db.Integer)
    Sport=db.Column(db.Integer)
    Entertainment=db.Column(db.Integer)
    Anders=db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class News(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    elasticsearch = db.Column(db.String(500))
    recommended = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class News_sel(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    news_id = db.Column(db.String(140))
    starttime = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    endtime = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    time_spent = db.Column(db.Interval)
    rating = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
