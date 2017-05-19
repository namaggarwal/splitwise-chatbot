from app.bot import BaseProcessor, BotProcessorFactory
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from splitwise.group import Group
from splitwise.debt import Debt
import random
from datetime import datetime, timedelta
from botsplitwise import BotSplitwise
from botexception import BotException
import constants
import processortype
from flask import current_app as app
import  pprint


def getInputFromRequest(input, param, error = constants.GENERAL_ERROR, required = False):
    if constants.RESULT in input:
        result = input[constants.RESULT]
        if constants.PARAMETERS in result:
            parameters = result[constants.PARAMETERS]
            paramvalue = ''
            if param in parameters:
                paramvalue = parameters[param]
            if paramvalue is not None and (paramvalue == "" or len(str(paramvalue))==0) and required:
                raise BotException(error)
            return paramvalue

    if not required:
        raise BotException(error)


class SplitwiseBotProcessorFactory(BotProcessorFactory):
    def __init__(self):
        super(SplitwiseBotProcessorFactory, self).__init__()

    def getProcessor(self, action):
        if action == processortype.TRANSACTION_PROCESSOR:
            return TransactionProcessor()
        elif action == processortype.GREETING_PROCESSOR:
            return GreetingProcessor()
        elif action == processortype.AGGREGATION_PROCESSOR:
            return AggregationProcessor()
        elif action == processortype.LISTEXPENSE_PROCESSOR:
            return ListTransactionProcessor()
        elif action == processortype.DEBT_PROCESSOR:
            return DebtProcessor()
        else:
            return UnknownProcessor()


class TransactionProcessor(BaseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing New Transaction Request")
        output = constants.OUTPUT
        splitwiseobj = BotSplitwise.getSplitwiseObj(input[constants.USER_ID])
        currentUser = splitwiseobj.getCurrentUser()
        friendslist = splitwiseobj.getFriends()

        userlist = []

        split = getInputFromRequest(input, constants.SPLIT, constants.ERROR_SPLIT, True)
        split = split.lower()
        if not split == constants.PAID or split == constants.OWE or split == constants.EQUALLY:
            raise BotException(constants.ERROR_WRONG_SPLIT)

        name = getInputFromRequest(input, constants.NAME, constants.ERROR_NAME, True)
        currency = getInputFromRequest(input, constants.CURRENCY)

        description = getInputFromRequest(input, constants.DESC)
        if description is None or description == "" or len(str(description))==0:
            description = constants.BOT

        amount = 0
        try:
            if constants.AMOUNT in currency:
                amount = currency[constants.AMOUNT]
        except Exception:
            amount = getInputFromRequest(input, constants.AMOUNT, self.getAmountError(split),True)


        group = str(getInputFromRequest(input, constants.GROUP))
        groupid = self.getGroupId(group, splitwiseobj.getGroups())
        expense = Expense()
        expense.setCost(amount)

        if not groupid == -1:
            expense.setGroupId(groupid)

        mode = split.lower()

        if description is None or description == "" or len(description) == 0:
            description = constants.BOT

        expense.setDescription(description)

        # current user
        paid, owed = self.getdistribution(mode, amount)
        cuser = self.getExpenseUser(currentUser, paid, owed)
        userlist.append(cuser)

        match = False
        for friend in friendslist:
            if friend.getFirstName().lower() == name.lower():
                expenseuser = self.getExpenseUser(friend, owed, paid)
                match = True
                if mode != constants.PAID and mode != constants.OWE:
                    expenseuser.setPaidShare(str(0))
                    expenseuser.setOwedShare(str(owed))

                output += friend.getFirstName()
                userlist.append(expenseuser)
                break

        if not match:
            return BotException(constants.NO_FRIEND_ERROR + name)

        expense.setUsers(userlist)
        expense = splitwiseobj.createExpense(expense)
        if expense.getId() is None or len(str(expense.getId())) == 0:
            raise BotException(constants.GENERAL_ERROR)
        app.logger.debug("New Expense is created")
        return output

    def getdistribution(self, mode, amount):
        if mode == constants.PAID:
            paid = amount
            owed = 0
        elif mode == constants.OWE:
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
        if not split == constants.PAID or split == constants.OWE:
            split = constants.WANT_TO_SPLIT
        errors.append(constants.AMOUNT_ERROR1)
        errors.append(constants.AMOUNT_ERROR2 + split)
        errors.append(constants.AMOUNT_ERROR3 + split + constants.QUESTION)
        return random.choice(errors)

    def getGroupId(self, group, groupList):
        if group is None or group == '' or len(group)==0:
            return -1
        group = group.lower()
        for groups in groupList:
            if group == groups.getName().lower():
                return groups.getId()

        return BotException(constants.ERROR_GROUP)

class GreetingProcessor(BaseProcessor):
    greetinglist = [constants.GREETING1, constants.GREETING2, constants.GREETING3]

    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing Greeting Request")
        return random.choice(self.greetinglist)


class AggregationProcessor(BaseProcessor):
    LIMIT = 'limit'
    DAYS = 'days'

    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing Aggregation Request")
        splitwiseobj = BotSplitwise.getSplitwiseObj(input[constants.USER_ID])
        currentuser = splitwiseobj.getCurrentUser()
        days = 7
        days = getInputFromRequest(input, constants.DAYS)
        if days == "" or len(str(days))==0:
            days = 7
        date = datetime.now() - timedelta(days= int(days))
        limit = 100
        allExpense = self.getExpenses(splitwiseobj, limit, date)
        dc = {}
        for expense in allExpense:
            if not expense.getDeletedAt() is None:
                continue
            owedshare = self.getOwedShare(expense.getUsers(), currentuser.getId())
            if not owedshare is None:
                code = expense.getCurrencyCode()
                if code in dc:
                    dc[code] += float(owedshare)
                else:
                    dc[code] = float(owedshare)
        output = currentuser.getDefaultCurrency() + constants.SPACE + constants.ZERO
        for key, value in dc.iteritems():
            output = str(key) + constants.SPACE + str(value) + constants.LINEBREAK
        app.logger.debug("Aggregation Request Processed")
        return output

    def getOwedShare(self, userList, currentUserId):
        for expenseuser in userList:
            if expenseuser.getId() == currentUserId:
                return expenseuser.getOwedShare()

    def getExpenses(self, splitwiseobj, limit, date):
        try:
            allExpense = splitwiseobj.getExpenses(limit=limit, dated_after=date)
            return allExpense
        except Exception:
            raise BotException(constants.GENERAL_ERROR)


class ListTransactionProcessor(BaseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing List Transaction Request")
        splitwiseobj = BotSplitwise.getSplitwiseObj(input[constants.USER_ID])
        currentuser = splitwiseobj.getCurrentUser()
        agg = AggregationProcessor()

        days = 7
        days = getInputFromRequest(input, constants.DAYS)
        if days == "" or len(str(days))==0:
            days = 7

        date = datetime.now() - timedelta(days=int(days))
        limit = 1000
        allExpense = agg.getExpenses(splitwiseobj, limit, date)
        outputdc = {}
        totalOwe = 0
        for expense in allExpense:
            if not expense.getDeletedAt() is None:
                continue
            owedshare = agg.getOwedShare(expense.getUsers(), currentuser.getId())
            if owedshare is None:
                continue
            totalOwe += float(owedshare)
            date = expense.getDate()
            dateob = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            dateob = dateob.strftime('%d-%m-%Y')
            output = expense.getDescription() + constants.SPACE + constants.EQUAL + constants.SPACE + \
                     expense.getCurrencyCode() + constants.SPACE + str(owedshare) + constants.LINEBREAK
            if dateob in outputdc:
                outputdc[dateob] += output
            else:
                outputdc[dateob] = output
        output = ""
        outputdc = sorted(outputdc.items())
        for key, value in outputdc:
            output += constants.LINEBREAK + constants.DATE + constants.SPACE + str(key) + constants.LINEBREAK
            output += value
        app.logger.debug("List Transaction Request Processed")
        return output


class UnknownProcessor(BaseProcessor):
    errorlist = [constants.UNKNOWN_ERROR2, constants.UNKNOWN_ERROR1]

    def __init__(self):
        pass

    def process(self, input):
        app.logger.debug("Processing Unknown Request")
        raise BotException(random.choice(self.errorlist))


class DebtProcessor(BaseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        splitwiseobj = BotSplitwise.getSplitwiseObj(input[constants.USER_ID])
        grouplist = splitwiseobj.getGroups()
        currentUser = splitwiseobj.getCurrentUser()
        friendId = -1
        name = getInputFromRequest(input, constants.NAME)
        if not name == "" or len(name) == 0:
            friendList = splitwiseobj.getFriends()
            id = self.getFriendId(friendList, name)
            if not id ==-1:
                friendId = id


        output = ''
        totaldictionary = {}
        for group in grouplist:
            debtList = group.getSimplifiedDebts()
            if debtList is None or len(debtList) == 0:
                continue
            output += constants.LINEBREAK + "In Group " + group.getName() + constants.LINEBREAK
            for debts in debtList:
                if debts.getFromUser() != currentUser.id:
                    continue
                if debts.getToUser() == friendId:
                    currency = debts.getCurrencyCode()
                    if currency in totaldictionary:
                        totaldictionary[currency]+= float(debts.getAmount())
                    else:
                        totaldictionary[currency] = float(debts.getAmount())

                user = splitwiseobj.getUser(debts.getToUser())
                output += user.getFirstName() + constants.SPACE + str(debts.getCurrencyCode()) + \
                          constants.SPACE + debts.getAmount() + constants.LINEBREAK

        resp = ''
        for key, value in totaldictionary.iteritems():
            resp += str(key) + constants.SPACE + str(value)+constants.LINEBREAK

        if not friendId == -1:
            output = resp

        return output

    def getFriendId(self, friendList, name):
        for friend in friendList:
            if friend.getFirstName().lower() == name.lower():
                return friend.getId()

        return -1
