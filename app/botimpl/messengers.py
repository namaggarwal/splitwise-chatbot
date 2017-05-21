from app.bot import BaseMessenger
from flask import url_for, current_app as app
import requests
import json

class FacebookMessenger(BaseMessenger):

    FACEBOOK_MESSAGE_URL = 'https://graph.facebook.com/v2.6/me/messages?'
    FACEBOOK_ACCOUNT_LINK_URL = 'https://graph.facebook.com/v2.6/me?access_token=PAGE_ACCESS_TOKEN&fields=recipient&account_linking_token=ACCOUNT_LINKING_TOKEN'

    def __init__(self,pageAccessToken=None,verifyToken=None):
        self.pageAccessToken = pageAccessToken
        self.verifyToken = verifyToken
        self.messageUrl =  FacebookMessenger.FACEBOOK_MESSAGE_URL+'access_token='+pageAccessToken
        self.accountUrl =  FacebookMessenger.FACEBOOK_ACCOUNT_LINK_URL.replace('PAGE_ACCESS_TOKEN',pageAccessToken)

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

    
    def getRecepientId(self,account_linking_token):

        url = self.accountUrl.replace("ACCOUNT_LINKING_TOKEN",account_linking_token)
        res = requests.get(url)
        res = json.loads(res.content)
        return res["recipient"]


    def sendLoginLink(self,receiverId):
        app.logger.debug("Sending Login Link")
        url = url_for("pages.splitwiseLogin",_external = True)
        messageData = {
            'recipient': {
                'id': int(receiverId)
            },
             
            'message': {
                "attachment":{
                    "type":"template",
                    "payload":{
                        "template_type":"button",
                        "text":"Please Login to Splitwise",
                        "buttons":[
                            {
                                "type": "account_link",
                                "url": url
                            }
                        ]
                    }
                },
            },
        }
        
        res = requests.post(self.messageUrl, json = messageData)
        if (res.status_code >= 400 and res.status_code <= 406):
            app.logger.debug("error occured while sending Login Link ")
            app.logger.debug(res.content)

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
        if(res.status_code>=400 and res.status_code<=406):
            app.logger.debug("error occured while sending request ")
            app.logger.debug(res.content)

