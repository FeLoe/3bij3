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
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s = {}'.format(digest, size)
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
    sport = db.Column(db.Integer)
    politiek = db.Column(db.Integer)
    economie = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class News(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    es_id = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class News_sel(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.es_id'))
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    rating = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
