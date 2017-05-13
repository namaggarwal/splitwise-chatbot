from app.bot import BaseMessenger

class FacebookMessenger(BaseMessenger):

    def __init__(self,pageAccessToken=None,verifyToken=None):
        self.pageAccessToken = pageAccessToken
        self.verifyToken = verifyToken

    def getVerifyToken(self):
        return self.verifyToken

    def getPageAccessToken(self):
        return self.pageAccessToken        

    def send(self,receiverId,message):
        pass