from app.bot import BaseProcessor, BotProcessorFactory


class SplitwiseBotProcessorFactory(BotProcessorFactory):

    def __init__(self):
        pass
    
    def getProcessor(self,action):
        if action == 'transaction':
            return TransactionProcessor()


class TransactionProcessor(BaseProcessor):

    def __init__(self):
        pass

    def process(self,input):
        pass
