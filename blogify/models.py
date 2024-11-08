from blogify import db, login_manager, app
from datetime import datetime
from flask_login import UserMixin   # provides default methods for login which flask_login expects to have 
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer 


@login_manager.user_loader
def load_user(user_id: int):
    return User.query.get(int(user_id))

# -- SQL models or data classes --
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    profile_pic = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def get_reset_token(self, expires_sec: int=1800): 
        s = Serializer(app.config['SECRET_KEY'], expires_in=expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User({self.id}, {self.username}, {self.email}, {self.profile_pic if self.profile_pic.startswith('http') else 'default.jpg'})"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    likes_count = db.Column(db.Integer, default=0)     # Likes counter
    dislikes_count = db.Column(db.Integer, default=0)  # Dislikes counter


    def __repr__(self):
        return f"Post({self.title}, {self.date_posted})"
    
class PostReaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reaction_type = db.Column(db.String(10), nullable=False)  # 'like' or 'dislike'
    date_reacted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_reaction'),)

    def __repr__(self):
        return f"PostReaction(post_id={self.post_id}, user_id={self.user_id}, reaction_type={self.reaction_type})"