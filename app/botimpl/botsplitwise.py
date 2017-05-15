from splitwise import Splitwise
from app.model import User
from flask import current_app as app

class BotSplitwise(object):

    def __init__(self):
        pass

    @staticmethod
    def getSplitwiseObj(user_id):
        splitwise = Splitwise(app.config['APP_KEY'], app.config['APP_SECRET'])
        user = User.getUserById(user_id)
        splitwise.setAccessToken(
            {
                "oauth_token": user.splitwise_token, "oauth_token_secret": user.splitwise_token_secret
            }
        )
        splitwise.setAccessToken(
            {
                "oauth_token": USER_TOKEN, "oauth_token_secret": USER_SECRET
            }
        )
        return splitwise
