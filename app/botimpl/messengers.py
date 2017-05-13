from app.bot import BaseMessenger
import json

class FacebookMessenger(BaseMessenger):

    def __init__(self,pageAccessToken=None,verifyToken=None):
        self.pageAccessToken = pageAccessToken
        self.verifyToken = verifyToken

    def getVerifyToken(self):
        return self.verifyToken

    def getPageAccessToken(self):
        return self.pageAccessToken 

    @staticmethod
    def getMessageText(data):
        
        message = None
        data = json.loads(data)
        if 'entry' in data and len(data['entry']) > 0:
            entry = data['entry'][0]
            if 'messaging' in entry:
                messaging = entry['messaging']
                
                if len(messaging) > 0 and 'message' in messaging[0]:
                    message = messaging[0]['message']['text']
        
        return message


    def send(self,receiverId,message):
        pass