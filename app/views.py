from flask import Blueprint, render_template, abort, request, current_app as app
from model import User
from botimpl import ChatBotController, FacebookMessenger

pages = Blueprint('pages', __name__,template_folder='templates')

@pages.route("/")
def home():
    return render_template("home.html")


@pages.route("/messenger",methods=['GET'])
def facebookVerify():

    #Create a messenger object
    messenger = FacebookMessenger(app.config['FACEBOOK_PAGE_ACCESS_TOKEN'],app.config['FACEBOOK_VERIFY_TOKEN'])

    #Get the request parameters from facebook
    verify_token = request.args['hub.verify_token']
    challenge = request.args['hub.challenge']

    #Verify that the request came from facebook
    if verify_token == messenger.getVerifyToken():
        #Return the challenge
        return challenge

    else:
        #Return Not found
        abort(404)


@pages.route("/messenger", methods=['POST'])
def facebookMessage():
    return ('',204)