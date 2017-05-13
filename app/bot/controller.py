class BotController(object):

    def __init__(self,senderId,converter,processorFactory,messenger):
        self.senderId = senderId
        self.converter = converter
        self.processorFactory = processorFactory
        self.messenger = messenger

    def parse(request):
        #NLP
        request = self.beforeConvert(request)
        action, structuredData = self.converter(request)

        #GenerateResponse
        action, structuredData = self.beforeProcess(action,structuredData)
        processor = self.processorFactory(action)
        response = processor.process(structuredData)
        
        #Send Message
        response = self.beforeSend(response)
        self.messenger.send(senderId,response)

    def beforeConvert(self,request):
        return request

    def beforeProcess(self,action,structuredData):
        return action, structuredData
    
    def beforeSend(self,response):
        return response