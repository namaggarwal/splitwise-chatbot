import unittest
from app.botimpl.processors import TransactionProcessor,AggregationProcessor



class TestProcessors(unittest.TestCase):

    # def test_TransactionProcessor(self):
    #     processorobj = TransactionProcessor()
    #     input = {}
    #     input['name'] = "e0013352"
    #     input['amount'] = 5
    #     input['split'] = 'equally'
    #     #input['description'] = 'Movie'
    #     output = processorobj.process(input)
    #     print output

    def test_aggregateProcessor(self):
        agg_obj = AggregationProcessor()
        input = {}
        input['days']=30
        input['limit']=25
        result = agg_obj.process(input)
        print result


if __name__ == '__main__':
    unittest.main()


