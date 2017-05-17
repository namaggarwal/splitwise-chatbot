from splitwise import Splitwise
from app.model import User
from flask import current_app as app

class BotSplitwise(object):

    def __init__(self):
        pass

    @staticmethod
    def getSplitwiseObj(user_id):
        splitwise = Splitwise(app.config['SPLITWISE_CONSUMER_KEY'], app.config['SPLITWISE_CONSUMER_SECRET'])
        user = User.getUserById(user_id)
        accessToken = {
                "oauth_token": str(user.splitwise_token), "oauth_token_secret": str(user.splitwise_token_secret)
            }
        splitwise.setAccessToken(accessToken)
        return splitwise
