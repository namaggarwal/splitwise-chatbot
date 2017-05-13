from app.bot import BotController
from converters import ApiAiConverter
from messengers import FacebookMessenger
from processors import SplitwiseBotProcessorFactory

class ChatBotController(BotController):

    def __init__(self,senderId):
        converter = ApiAiConverter()
        messenger = FacebookMessenger()
        processorFactory = SplitwiseBotProcessorFactory()
        super(ChatBotController, self).__init__(senderId,converter,processorFactory,messenger)
