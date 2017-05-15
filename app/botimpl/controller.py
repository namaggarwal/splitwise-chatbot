from app.bot import BotController
from converters import ApiAiConverter
from messengers import FacebookMessenger
from processors import SplitwiseBotProcessorFactory
from flask import current_app as app
import pprint

class ChatBotController(BotController):

    def __init__(self,senderId):
        converter = ApiAiConverter(app.config['API_AI_CLIENT_ACCESS_TOKEN'])
        messenger = FacebookMessenger(app.config['FACEBOOK_PAGE_ACCESS_TOKEN'],app.config['FACEBOOK_VERIFY_TOKEN'])
        processorFactory = SplitwiseBotProcessorFactory()
        super(ChatBotController, self).__init__(senderId,converter,processorFactory,messenger)
    
    def beforeConvert(self,request):
        request = {
            'session_id': FacebookMessenger.getSenderId(request),
            'query': FacebookMessenger.getMessageText(request)
        }
        return request

    def beforeProcess(self,action,structuredData):
        structuredData['user_id'] = self.senderId
        return action, structuredData

    def beforeSend(self,response):
        return response