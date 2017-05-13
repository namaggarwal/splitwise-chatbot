from flask import Blueprint, render_template
from model import User
from botimpl import ChatBotController

pages = Blueprint('pages', __name__,template_folder='templates')

@pages.route("/")
def home():

    return render_template("home.html")

