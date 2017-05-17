from flask import Blueprint, render_template, abort, request, redirect, url_for, session, current_app as app
from model import User
from botimpl import ChatBotController, FacebookMessenger
import json
from splitwise import Splitwise
import urllib
from app.botimpl.botexception import BotException
from  app.botimpl import constants


pages = Blueprint('pages', __name__,template_folder='templates')

FACEBOOK_ACCOUNT_LINKING_TOKEN = "account_linking_token"
FACEBOOK_REDIRECT_URI = "redirect_uri"

SPLITWISE_SECRET = "splitwise_secret"
SPLITWISE_OAUTH_TOKEN = "oauth_token"
SPLITWISE_OAUTH_VERIFIER = "oauth_verifier"
SPLITWISE_OAUTH_TOKEN_SECRET = "oauth_token_secret"



def askUserToLogin(senderId):
    messenger = FacebookMessenger(app.config['FACEBOOK_PAGE_ACCESS_TOKEN'],app.config['FACEBOOK_VERIFY_TOKEN'])
    messenger.sendLoginLink(senderId)

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


def checkFirstTimeLogin(data):
    entryList = data['entry']
    messagingList = entryList[0]['messaging']
    messagingDictionary = messagingList[0]
    if 'account_linking' in messagingDictionary:
        return True
    return  False


@pages.route("/messenger", methods=['POST'])
def facebookMessage():
    bot = ''
    senderId = ''
    try:
        data = json.loads(request.data)
        senderId = FacebookMessenger.getSenderId(data)
        if not User.getUserById(senderId):
            askUserToLogin(senderId)
        else:
            bot = ChatBotController(senderId)
            if checkFirstTimeLogin(data):
                bot.messenger.send(senderId, constants.LOGIN_SUCCESS)
                return ('',204)

            bot.parse(data)
    except BotException as e:
        bot.messenger.send(senderId, str(e))
        app.logger.debug("BotException Occured " + str(e))
    except Exception as e:
        bot.messenger.send(senderId, constants.GENERAL_ERROR)
        app.logger.debug("Exception Occured "+str(e))
    return ('',204)


@pages.route("/splitwise",methods=['GET'])
def splitwiseLogin():
    
    if SPLITWISE_OAUTH_TOKEN not in request.args or SPLITWISE_OAUTH_VERIFIER not in request.args:

        if FACEBOOK_ACCOUNT_LINKING_TOKEN not in request.args or FACEBOOK_REDIRECT_URI not in request.args:
            abort(404)

        app.logger.debug("User trying to provide splitwise access")
        sObj = Splitwise(app.config["SPLITWISE_CONSUMER_KEY"],app.config["SPLITWISE_CONSUMER_SECRET"])
        url, secret = sObj.getAuthorizeURL()
        session[SPLITWISE_SECRET] = secret
        session[FACEBOOK_ACCOUNT_LINKING_TOKEN] = request.args[FACEBOOK_ACCOUNT_LINKING_TOKEN]
        session[FACEBOOK_REDIRECT_URI] = request.args[FACEBOOK_REDIRECT_URI]
        return redirect(url)

    else:
        oauth_token    = request.args.get(SPLITWISE_OAUTH_TOKEN)
        oauth_verifier = request.args.get(SPLITWISE_OAUTH_VERIFIER)
        sObj = Splitwise(app.config["SPLITWISE_CONSUMER_KEY"],app.config["SPLITWISE_CONSUMER_SECRET"])
        access_token = sObj.getAccessToken(oauth_token,session[SPLITWISE_SECRET],oauth_verifier)
        messenger = FacebookMessenger(app.config['FACEBOOK_PAGE_ACCESS_TOKEN'],app.config['FACEBOOK_VERIFY_TOKEN'])
        facebookReceipientId = messenger.getRecepientId(session[FACEBOOK_ACCOUNT_LINKING_TOKEN])

        authorization_code = None
        if facebookReceipientId is not None:

            user = User.query.filter_by(user_id=facebookReceipientId).first()
            if not user:
                user = User()
                user.user_id = str(facebookReceipientId)
            user.splitwise_token = access_token[SPLITWISE_OAUTH_TOKEN]
            user.splitwise_token_secret = access_token[SPLITWISE_OAUTH_TOKEN_SECRET]
            user.save()
            authorization_code = 'success'

        redirect_url = urllib.unquote(session[FACEBOOK_REDIRECT_URI])
        if authorization_code:
            redirect_url += '&authorization_code='+authorization_code
        return redirect(redirect_url)


            