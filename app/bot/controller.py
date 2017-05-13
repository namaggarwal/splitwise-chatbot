class BotController(object):

    def __init__(self,senderId,converter,processorFactory,messenger):
        self.senderId = senderId
        self.converter = converter
        self.processorFactory = processorFactory
        self.messenger = messenger

    def parse(self,request):
        #NLP
        request = self.beforeConvert(request)
        action, structuredData = self.converter.convert(request)

        #GenerateResponse
        action, structuredData = self.beforeProcess(action,structuredData)
        processor = self.processorFactory.getProcessor(action)
        response = processor.process(structuredData)
        
        #Send Message
        response = self.beforeSend(response)
        self.messenger.send(self.senderId,response)

    def beforeConvert(self,request):
        return request

    def beforeProcess(self,action,structuredData):
        return action, structuredData
    
    def beforeSend(self,response):
        return response