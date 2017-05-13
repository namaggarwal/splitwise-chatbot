from app.bot import BaseConverter
import apiai
import json

class ApiAiConverter(BaseConverter):

    def __init__(self,client_access_token):
        self.ai = apiai.ApiAI(client_access_token)
        self.request = self.ai.text_request()
        self.request.land = 'en'
    
    @staticmethod
    def getAction(response):
        action = None

        if 'result' in response:
            result = response['result']
            if 'action' in result:
                action = result['action']
        
        return action


    def convert(self,request):

        self.request.session_id = request['session_id']
        self.request.query  = request['query']
        response = self.request.getresponse()
        response = json.loads(response.read())
        return ApiAiConverter.getAction(response), response
        