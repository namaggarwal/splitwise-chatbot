from middleware import db, bcrypt, login_manager

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(128), unique=True)
    splitwise_token = db.Column(db.String(128), nullable=False)
    splitwise_token_secret = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.user_id

    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @staticmethod
    def getUserById(user_id):
        return User.query.filter_by(user_id= user_id).first()

    
