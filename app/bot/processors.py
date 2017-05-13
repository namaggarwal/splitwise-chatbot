class BotProcessorFactory(object):

    '''
    Factory class to give the appropriate processor based on action
    '''
    
    def __init__(self):
        pass
        
    def getProcessor(self,action):
        '''
        Returns an object of Processor
        '''
        pass



class BaseProcessor(object):
    '''
    BaseProcessor class to process actions
    Input: Structured JSON data
    returns response
    '''

    def process(self,input):
        pass

