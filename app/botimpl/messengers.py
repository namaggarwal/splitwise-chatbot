from app.bot import BaseMessenger
import requests

class FacebookMessenger(BaseMessenger):

    FACEBOOK_MESSAGE_URL = 'https://graph.facebook.com/v2.6/me/messages?'

    def __init__(self,pageAccessToken=None,verifyToken=None):
        self.pageAccessToken = pageAccessToken
        self.verifyToken = verifyToken
        self.messageUrl =  FacebookMessenger.FACEBOOK_MESSAGE_URL+'access_token='+pageAccessToken

    def getVerifyToken(self):
        return self.verifyToken

    def getPageAccessToken(self):
        return self.pageAccessToken 

    @staticmethod
    def getSenderId(data):

        senderId = None
        if 'entry' in data and len(data['entry']) > 0:
            entry = data['entry'][0]
            if 'messaging' in entry:
                messaging = entry['messaging']
                if len(messaging) > 0 and 'sender' in messaging[0]:
                    senderId = messaging[0]['sender']['id']

        return senderId

    @staticmethod
    def getMessageText(data):
        
        message = None
        if 'entry' in data and len(data['entry']) > 0:
            entry = data['entry'][0]
            if 'messaging' in entry:
                messaging = entry['messaging']
                
                if len(messaging) > 0 and 'message' in messaging[0]:
                    message = messaging[0]['message']['text']
        
        return message


    def send(self,receiverId,message):
        
        messageData = {
            'recipient': {
                'id': int(receiverId)
            },
            'message': {
                'text': message
            }
        }
        res = requests.post(self.messageUrl, json = messageData)

