from app.bot import BaseProcessor, BotProcessorFactory
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from splitwise.group import Group
from splitwise.debt import Debt
from datetime import datetime, timedelta
from botsplitwise import BotSplitwise
from botexception import BotException, LoginException
from constants import BotConstants, ErrorMessages
from flask import current_app as app
import random

class SplitwiseBotProcessorFactory(BotProcessorFactory):
    class ProcessorType(object):
        '''
        Processor Type
        '''
        TRANSACTION_PROCESSOR = 'transaction'
        GREETING_PROCESSOR = 'greeting'
        AGGREGATION_PROCESSOR = 'aggregation'
        LISTEXPENSE_PROCESSOR = 'listexpense'
        DEBT_PROCESSOR = "debt"
        HELP_PROCESSOR = "help"

    def __init__(self):
        super(SplitwiseBotProcessorFactory, self).__init__()

    def getProcessor(self, action):

        if action == SplitwiseBotProcessorFactory.ProcessorType.TRANSACTION_PROCESSOR:
            return TransactionProcessor()

        elif action == SplitwiseBotProcessorFactory.ProcessorType.GREETING_PROCESSOR:
            return GreetingProcessor()

        elif action == SplitwiseBotProcessorFactory.ProcessorType.AGGREGATION_PROCESSOR:
            return AggregationProcessor()

        elif action == SplitwiseBotProcessorFactory.ProcessorType.LISTEXPENSE_PROCESSOR:
            return ListTransactionProcessor()

        elif action == SplitwiseBotProcessorFactory.ProcessorType.DEBT_PROCESSOR:
            return DebtProcessor()

        elif action == SplitwiseBotProcessorFactory.ProcessorType.HELP_PROCESSOR:
            return HelpProcessor()

        else:
            return UnknownProcessor()


class SplitwiseProcessor(BaseProcessor):
    @staticmethod
    def getInputFromRequest(input, param, error=ErrorMessages.GENERAL, required=False):

        if BotConstants.RESULT in input:

            result = input[BotConstants.RESULT]

            if BotConstants.PARAMETERS in result:

                parameters = result[BotConstants.PARAMETERS]

                param_value = ''
                if param in parameters:
                    param_value = parameters[param]

                if param_value is not None and (param_value == "" or len(str(param_value)) == 0) and required:
                    raise BotException(error)

                return param_value

        if not required:
            raise BotException(error)

    @staticmethod
    def getExpenses(splitwise_obj, limit, date):
        try:
            expenses = splitwise_obj.getExpenses(limit=limit, dated_after=date)
            return expenses
        except Exception:
            raise BotException(ErrorMessages.GENERAL)

    @staticmethod
    def getOwedShare(users, current_user_id):
        for expense_user in users:
            if expense_user.getId() == current_user_id:
                return expense_user.getOwedShare()

    @staticmethod
    def getSplitwiseObject(input):
        if not BotConstants.USER_ID in input:
            raise LoginException("You are not logged in")

        try:
            splitwise_obj = BotSplitwise.getSplitwiseObj(input[BotConstants.USER_ID])
            return splitwise_obj
        except Exception as e:
            raise LoginException("You are not logged in")


class TransactionProcessor(SplitwiseProcessor):
    AMOUNT_ERRORS = [
        "Please enter the amount",
        "I don't know the amount you {split}?",
        "How much did you {split}?"
    ]

    class SplitType(object):

        SPLIT = 'split'
        PAID = 'paid'
        OWE = 'owe'

        @staticmethod
        def getSplitList():
            return [TransactionProcessor.SplitType.SPLIT, TransactionProcessor.SplitType.PAID,
                    TransactionProcessor.SplitType.OWE]

    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing New Transaction Request")

        output = BotConstants.NEW_EXPENSE_OUTPUT
        splitwise_obj = SplitwiseProcessor.getSplitwiseObject(input)

        current_user = splitwise_obj.getCurrentUser()
        friends_list = splitwise_obj.getFriends()

        user_list = []
        split = SplitwiseProcessor.getInputFromRequest(input, TransactionProcessor.SplitType.SPLIT, ErrorMessages.SPLIT,
                                                       True)
        split = split.lower()

        if split not in TransactionProcessor.SplitType.getSplitList():
            raise BotException(ErrorMessages.WRONG_SPLIT)

        name = SplitwiseProcessor.getInputFromRequest(input, BotConstants.NAME, ErrorMessages.NAME, True)
        currency = SplitwiseProcessor.getInputFromRequest(input, BotConstants.CURRENCY)
        description = SplitwiseProcessor.getInputFromRequest(input, BotConstants.DESCRIPTION)

        if description == "":
            description = BotConstants.FROM_BOT

        amount = 0

        if BotConstants.AMOUNT in currency:
            amount = currency[BotConstants.AMOUNT]
        else:
            amount = SplitwiseProcessor.getInputFromRequest(input, BotConstants.AMOUNT, self.getAmountError(split),
                                                            True)

        group = str(SplitwiseProcessor.getInputFromRequest(input, BotConstants.GROUP))
        group_id = self.getGroupId(group, splitwise_obj.getGroups())

        expense = Expense()
        expense.setCost(amount)

        if not group_id == -1:
            expense.setGroupId(group_id)

        mode = split.lower()

        expense.setDescription(description)

        # current user
        paid, owed = self.getDistribution(mode, amount)
        expense_user = self.getExpenseUser(current_user, paid, owed)
        user_list.append(expense_user)

        match = False
        for friend in friends_list:
            if friend.getFirstName().lower() == name.lower():
                expense_user = self.getExpenseUser(friend, owed, paid)
                match = True
                if mode != TransactionProcessor.SplitType.PAID and mode != TransactionProcessor.SplitType.OWE:
                    expense_user.setPaidShare(str(0))
                    expense_user.setOwedShare(str(owed))

                output += friend.getFirstName()
                user_list.append(expense_user)
                break

        if not match:
            raise BotException(ErrorMessages.NO_FRIEND.format(name=name))

        expense.setUsers(user_list)

        expense = splitwise_obj.createExpense(expense)

        if expense.getId() is None:
            raise BotException(ErrorMessages.GENERAL)

        app.logger.debug("New Expense is created")

        return output

    def getDistribution(self, mode, amount):

        if mode == TransactionProcessor.SplitType.PAID:
            paid = amount
            owed = 0
        elif mode == TransactionProcessor.SplitType.OWE:
            paid = 0
            owed = amount
        else:
            paid = amount
            owed = amount / 2.0

        return paid, owed

    def getExpenseUser(self, friend, paid, owed):
        user = ExpenseUser()
        user.setId(friend.getId())
        user.setPaidShare(str(paid))
        user.setOwedShare(str(owed))

        return user

    def getAmountError(self, split):
        errors = []
        if not split == TransactionProcessor.SplitType.PAID or split == TransactionProcessor.SplitType.OWE:
            split = BotConstants.WANT_TO_SPLIT

        return random.choice(TransactionProcessor.AMOUNT_ERRORS).format(split=split)

    def getGroupId(self, group_name, groups):

        if group_name is None or group_name == '' or len(group_name) == 0:
            return -1
        group_name = group_name.lower()
        for group in groups:
            if group_name == group.getName().lower():
                return group.getId()

        raise BotException(ErrorMessages.GROUP)


class GreetingProcessor(SplitwiseProcessor):
    greetings = [
        "Hey, How can i help you?",
        "Hello, may i help you in any way?",
        "Hi, do you need any help?"
    ]

    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing Greeting Request")
        return random.choice(GreetingProcessor.greetings)


class AggregationProcessor(SplitwiseProcessor):
    LIMIT = 'limit'
    DAYS = 'days'

    def __init__(self):
        pass

    def process(self, input):

        app.logger.debug("Processing Aggregation Request")

        splitwise_obj = SplitwiseProcessor.getSplitwiseObject(input)
        current_user = splitwise_obj.getCurrentUser()

        days = SplitwiseProcessor.getInputFromRequest(input, BotConstants.DAYS)

        if days == "" or len(str(days)) == 0:
            days = 7

        limit = 100

        date = datetime.now() - timedelta(days=int(days))

        allExpense = SplitwiseProcessor.getExpenses(splitwise_obj, limit, date)

        expenses = {}

        for expense in allExpense:
            if not expense.getDeletedAt() is None:
                continue

            owed_share = SplitwiseProcessor.getOwedShare(expense.getUsers(), current_user.getId())

            if not owed_share is None:

                currency_code = expense.getCurrencyCode()
                if currency_code in expenses:
                    expenses[currency_code] += float(owed_share)
                else:
                    expenses[currency_code] = float(owed_share)

        output = ''
        for key, value in expenses.iteritems():
            output += str(key) + BotConstants.SPACE + str(value) + BotConstants.LINEBREAK

        if output == '':
            output = current_user.getDefaultCurrency() + BotConstants.SPACE + BotConstants.ZERO

        app.logger.debug("Aggregation Request Processed")

        return output


class ListTransactionProcessor(SplitwiseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing List Transaction Request")

        splitwise_obj = SplitwiseProcessor.getSplitwiseObject(input)
        current_user = splitwise_obj.getCurrentUser()

        days = SplitwiseProcessor.getInputFromRequest(input, BotConstants.DAYS)
        if days == "" or len(str(days)) == 0:
            days = 7
        limit = 1000

        date = datetime.now() - timedelta(days=int(days))

        allExpense = SplitwiseProcessor.getExpenses(splitwise_obj, limit, date)

        expenses = {}

        totalOwe = 0
        for expense in allExpense:
            if expense.getDeletedAt():
                continue

            owedshare = SplitwiseProcessor.getOwedShare(expense.getUsers(), current_user.getId())

            if owedshare is None:
                continue

            totalOwe += float(owedshare)
            date = datetime.strptime(expense.getDate(), '%Y-%m-%dT%H:%M:%SZ').strftime('%d-%m-%Y')
            output = expense.getDescription() + BotConstants.SPACE + BotConstants.EQUAL + BotConstants.SPACE + \
                     expense.getCurrencyCode() + BotConstants.SPACE + str(owedshare) + BotConstants.LINEBREAK
            if date in expenses:
                expenses[date] += output
            else:
                expenses[date] = output

        output = ""
        expenses = sorted(expenses.items())

        for date, value in expenses:
            output += BotConstants.LINEBREAK + BotConstants.DATE + BotConstants.SPACE + str(
                date) + BotConstants.LINEBREAK
            output += value
        app.logger.debug("List Transaction Request Processed")
        return output


class UnknownProcessor(SplitwiseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing Unknown Request")
        raise BotException(random.choice(ErrorMessages.UNKNOWN))


class DebtProcessor(SplitwiseProcessor):
    def __init__(self):
        pass

    def process(self, input):

        splitwise_obj = SplitwiseProcessor.getSplitwiseObject(input)
        groups = splitwise_obj.getGroups()
        current_user = splitwise_obj.getCurrentUser()
        friend_id = -1
        name = SplitwiseProcessor.getInputFromRequest(input, BotConstants.NAME)

        if not name == "" or len(name) == 0:
            friends = splitwise_obj.getFriends()
            id = self.getFriendId(friends, name)
            if not id == -1:
                friend_id = id

        output_group_heading = ''
        expenses = {}
        output = ''
        for group in groups:
            debts = group.getSimplifiedDebts()
            debt_found = False
            if debts is None:
                continue
            output_group_heading = BotConstants.LINEBREAK + BotConstants.In_GROUP + BotConstants.SPACE \
                                   + group.getName() + BotConstants.LINEBREAK
            debt_output = ''
            for debt in debts:
                if (debt.getFromUser() != current_user.id) and (debt.getToUser() != current_user.id):
                    continue
                if debt.getToUser() == friend_id or debt.getFromUser() == friend_id:
                    currency = debt.getCurrencyCode()
                    debtamount = float(debt.getAmount())
                    if currency in expenses:
                        if debt.getToUser() == current_user.getId():
                            expenses[currency] -= debtamount
                        else:
                            expenses[currency] += debtamount
                    else:
                        if debt.getToUser() == current_user.getId():
                            expenses[currency] = -debtamount
                        else:
                            expenses[currency] = debtamount
                amount = ""
                debt_found = True
                if debt.getToUser() == current_user.getId():
                    user = splitwise_obj.getUser(debt.getFromUser())
                    amount = "-" + debt.getAmount()
                else:
                    amount = debt.getAmount()
                    user = splitwise_obj.getUser(debt.getToUser())

                debt_output += user.getFirstName() + BotConstants.SPACE + str(debt.getCurrencyCode()) + \
                               BotConstants.SPACE + amount + BotConstants.LINEBREAK
            if debt_found:
                output += output_group_heading + debt_output

        resp = ''
        for key, value in expenses.iteritems():
            resp += str(key) + BotConstants.SPACE + str(value) + BotConstants.LINEBREAK

        if not friend_id == -1:
            output = resp

        return output

    def getFriendId(self, friends, name):
        for friend in friends:
            if friend.getFirstName().lower() == name.lower():
                return friend.getId()

        return -1


class HelpProcessor(SplitwiseProcessor):
    help = "How much do i owe [John] \n" \
           "How much did i spend in last 7 days\n" \
    "List/show my bills for last 5 days\n" \
    "I paid John 10$ [in group Hangout]\n" \
    "I owe John 10$ [in group Hangout]"


    help_fix = "You can ask me following queries \n\n"


    @staticmethod
    def getHelp():
        return HelpProcessor.help_fix + HelpProcessor.help

    def __init__(self):
        pass


    def process(self, input):
        app.logger.debug("Processing help request")
        return HelpProcessor.getHelp()
