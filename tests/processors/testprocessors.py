import unittest
from app.botimpl.processors import TransactionProcessor,AggregationProcessor, UnknownProcessor
from app.botimpl.processors import DebtProcessor, GreetingProcessor, ListTransactionProcessor
from app.botimpl.botexception import BotException
import testdata
from app import app


class TestProcessors(unittest.TestCase):

    def test_TransactionProcessor(self):
        with app.app_context():
            processorobj = TransactionProcessor()
            output = processorobj.process(testdata.transaction)
            print output

    def test_aggregateProcessor(self):
        with app.app_context():
            agg_obj = AggregationProcessor()
            result = agg_obj.process(testdata.aggregation)
            print result

    def test_listTransactionProcessor(self):
        with app.app_context():
            obj = ListTransactionProcessor()
            output = obj.process(testdata.listtransaction)
            print output

    def test_GreetingProcessor(self):
        with app.app_context():
            obj = GreetingProcessor()
            output = obj.process(testdata.greeting)
            print output


    def test_debtProcessor(self):
        with app.app_context():
            debt_obj = DebtProcessor()
            output = debt_obj.process(testdata.debt)
            print output

    def test_unknownProcessor(self):
        with app.app_context():
            obj = UnknownProcessor()
            with self.assertRaises(BotException) as excep:
                obj.process(testdata.unknown)
            print "Error thrown:- "+str(excep.exception)



if __name__ == '__main__':
    unittest.main()


