import os
from flask import Flask
from middleware import db, bcrypt, login_manager
from views import pages

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')

if os.path.exists("instance/config.py"):
    app.config.from_pyfile('config.py')

if os.environ.get('APP_CONFIG_FILE', None):
    app.config.from_envvar('APP_CONFIG_FILE')


### Flask Configurations ####
app.secret_key = app.config["FLASK_SECRET_KEY"]


### SQL Alchemy Configurations ####
app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]
db.init_app(app)

#### Login Manager Configurations ####
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view =  "pages.login"

### Bcrypt Configurations ###
bcrypt.init_app(app)

### Blueprints Configuration ###
app.register_blueprint(pages)
