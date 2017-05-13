import unittest
from app.botimpl.processors import TransactionProcessor



class TestProcessors(unittest.TestCase):

    def test_TransactionProcessor(self):
        processorobj = TransactionProcessor()
        input = {}
        input['name'] = "e0013352"
        input['amount'] = 5
        input['split'] = 'equally'
        #input['description'] = 'Movie'
        output = processorobj.process(input)
        print output


if __name__ == '__main__':
    unittest.main()


