import os
from flask import Flask
from middleware import db, bcrypt, login_manager
from views import pages
from werkzeug.wsgi import DispatcherMiddleware

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')

if os.path.exists("instance/config.py"):
    app.config.from_pyfile('config.py')

if os.environ.get('APP_CONFIG_FILE', None):
    app.config.from_envvar('APP_CONFIG_FILE')


### Flask Configurations ####
app.secret_key = app.config["FLASK_SECRET_KEY"]


#### Set the correct application root ####
if app.config["APPLICATION_ROOT"] is not None and app.config["APPLICATION_ROOT"] != "":
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {app.config["APPLICATION_ROOT"]:app.wsgi_app})
else:
    app.config["APPLICATION_ROOT"] = None

#### Proxy fix if your app is behind Proxy #####
if app.config["BEHIND_PROXY"]:
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

### SQL Alchemy Configurations ####
app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]
db.init_app(app)

### Bcrypt Configurations ###
bcrypt.init_app(app)

### Blueprints Configuration ###
app.register_blueprint(pages)
