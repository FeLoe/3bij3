from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from time import time
import jwt
from app import app
from sqlalchemy_utils import aggregated

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index=True, unique = True)
    password_hash = db.Column(db.String(128))
    group = db.Column(db.Integer)
    first_login = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    points_stories = db.relationship('Points_stories', backref = 'user', lazy = 'dynamic')
    points_invites = db.relationship('Points_invites', backref = 'user', lazy = 'dynamic')
    points_ratings = db.relationship('Points_ratings', backref = 'user', lazy = 'dynamic')
    points_logins = db.relationship('Points_logins', backref = 'user', lazy = 'dynamic')
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

    @aggregated('logins_sum', db.Column(db.Integer))
    def sum_logins(self):
        return db.func.sum(Points_logins.points_logins)
    logins_sum = db.relationship('Points_logins')
    @aggregated('ratings_sum', db.Column(db.Numeric(5,1)))
    def sum_ratings(self):
        return db.func.sum(Points_ratings.points_ratings)
    ratings_sum = db.relationship('Points_ratings')
    @aggregated('invites_sum', db.Column(db.Integer))
    def sum_invites(self):
        return db.func.sum(Points_invites.points_invites)
    invites_sum = db.relationship('Points_invites')
    @aggregated('stories_sum', db.Column(db.Integer))
    def sum_stories(self):
        return db.func.sum(Points_stories.points_stories)
    stories_sum = db.relationship('Points_stories')
    
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
    url = db.Column(db.String(500))
    
class News_sel(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    news_id = db.Column(db.String(140))
    starttime = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    endtime = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    time_spent = db.Column(db.Interval)
    rating = db.Column(db.Integer, default = 0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User_invite(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    stories_read = db.Column(db.Integer, default = 0)
    times_logged_in = db.Column(db.Integer, default = 0)
    user_host = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_guest = db.Column(db.String(64), db.ForeignKey('user.username'))

class Points_stories(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    points_stories = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Points_invites(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_guest_new = db.Column(db.String(64), db.ForeignKey('user_invite.user_guest'))
    points_invites = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Points_ratings(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    points_ratings = db.Column(db.Numeric(5,1), default = 0.0)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Points_logins(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    points_logins = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_agent = db.Column(db.String(500))
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

