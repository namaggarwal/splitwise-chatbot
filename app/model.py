from middleware import db, bcrypt, login_manager
from sqlalchemy.ext.hybrid import hybrid_property


@login_manager.user_loader
def load_user(userid):
    return User.query.filter(User.id==userid).first()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True)
    _password = db.Column(db.String(120))


    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)


    def __repr__(self):
        return '<User %r>' % self.email

    def save(self):
        db.session.add(self)
        db.session.commit()

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
