from app.bot import BaseProcessor, BotProcessorFactory
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from splitwise.group import Group
from splitwise.debt import Debt
import random
from datetime import datetime, timedelta
from botsplitwise import BotSplitwise

DESC = "description"
SPLIT = "split"
PAID = "paid"
OWE = "owe"
AMOUNT = 'amount'
OUTPUT = "New Expense has been added between You and "
EQUALLY = "equally"
BOT = "From Bot"
NAME = "name"
GREETING1 = "Hey, How can i help you?"
GREETING2 = "Hello, may i help you any way?"
GREETING3 = "Hi, do you need any help?"
SPACE = " "
EXPENSE_SUMMARY = 'Here is the summary of your expense'
YOU = "You"
FOR = "for"


class SplitwiseBotProcessorFactory(BotProcessorFactory):
    def __init__(self):
        super(SplitwiseBotProcessorFactory, self).__init__()

    def getProcessor(self, action):
        if action == 'transaction':
            return TransactionProcessor()
        elif action == 'greeting':
            return GreetingProcessor()
        elif action == 'aggregation':
            return AggregationProcessor()
        elif action == 'listexpense':
            return ListTransactionProcessor()
        else:
            return UnknownProcessor()


class TransactionProcessor(BaseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        output = OUTPUT
        splitwiseobj = BotSplitwise.getSplitwiseObj(input['user_id'])
        currentUser = splitwiseobj.getCurrentUser()
        friendslist = splitwiseobj.getFriends()

        userlist = []
        if 'result' in input:
            result = input['result']
            if 'parameters' in result:
                parameters = result['parameters']
                if not AMOUNT in parameters:
                    return "Please enter the amount"
                if not NAME in parameters:
                    return "Please enter the name of the person you "
                name = str(parameters[NAME])
                split = str(parameters[SPLIT])
                amount = int(parameters[AMOUNT])

        #amount = input.get(AMOUNT)

        expense = Expense()
        expense.setCost(amount)

        mode = split.lower()

        description = ''
        if DESC in input:
            description = input.get(DESC)
        else:
            description = BOT

        expense.setDescription(description)

        # current user
        paid, owed = self.getDistribution(mode, amount)
        cuser = self.getExpenseUser(currentUser, paid, owed)
        userlist.append(cuser)

        for friend in friendslist:
            if friend.getFirstName().lower() == name.lower():
                expenseuser = self.getExpenseUser(friend, owed, paid)
                if mode != PAID and mode != OWE:
                    expenseuser.setPaidShare(str(0))
                    expenseuser.setOwedShare(str(owed))

                output += friend.getFirstName()
                userlist.append(expenseuser)
                break

        expense.setUsers(userlist)
        expense = splitwiseobj.createExpense(expense)
        return output

    def getDistribution(self, mode, amount):
        if mode == PAID:
            paid = amount
            owed = 0
        elif mode == OWE:
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


class GreetingProcessor(BaseProcessor):
    def __init__(self):
        self.greetings = []
        self.greetings.append(GREETING1)
        self.greetings.append(GREETING2)
        self.greetings.append(GREETING3)

    def process(self, input):
        return random.choice(self.greetings)


class AggregationProcessor(BaseProcessor):
    LIMIT = 'limit'
    DAYS = 'days'

    def __init__(self):
        pass

    def process(self, input):
        splitwiseobj = BotSplitwise.getSplitwiseObj(input['user_id'])
        currentuser = splitwiseobj.getCurrentUser()
        days = 7
        if 'result' in input:
            result = input['result']
            if 'parameters' in result:
                parameters = result['parameters']
                days = int(parameters[self.DAYS])

        date = datetime.now() - timedelta(days=days)
        limit = 100
        allExpense = splitwiseobj.getExpenses(limit=limit, dated_after=date)
        dc = {}
        for expense in allExpense:
            owedshare = self.getOwedShare(expense.getUsers(), currentuser.getId())
            if not owedshare is None:
                code = expense.getCurrencyCode()
                if code in dc:
                    dc[code] += float(owedshare)
                else:
                    dc[code] = float(owedshare)
        output = currentuser.getDefaultCurrency()+" 0.0"
        for key, value in dc.iteritems():
            output = str(key) + SPACE + str(value) + "\n"

        return output

    def getOwedShare(self, userList, currentUserId):
        for expenseuser in userList:
            if expenseuser.getId() == currentUserId:
                return expenseuser.getOwedShare()


class ListTransactionProcessor(BaseProcessor):
    LIMIT = 'limit'
    DAYS = 'days'

    def __init__(self):
        pass

    def process(self, input):
        splitwiseobj = BotSplitwise.getSplitwiseObj(input['user_id'])
        currentuser = splitwiseobj.getCurrentUser()
        days = 7
        if self.DAYS in input:
            days = input.get(self.DAYS)
        date = datetime.now() - timedelta(days=days)
        limit = 100

        if self.LIMIT in input:
            limit = input.get(self.LIMIT)
        allExpense = splitwiseobj.getExpenses(limit=limit, dated_after=date)
        output = EXPENSE_SUMMARY + '\n'
        agg = AggregationProcessor()
        for expense in allExpense:
            date = expense.getDate()
            dateob = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            output += dateob.strftime('%Y-%m-%d') + ": "
            output += YOU + SPACE + OWE + SPACE + expense.getCurrencyCode() + SPACE
            owedshare = agg.getOwedShare(expense.getUsers(), currentuser.getId())
            if owedshare is None:
                owedshare = 0.0
            output += str(owedshare) + SPACE + FOR + SPACE + expense.getDescription() + "\n"

        return output


class DebtProcessor(BaseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        splitwiseobj = Splitwise(APP_KEY, APP_SECRET)
        splitwiseobj.setAccessToken(
            {
                "oauth_token": USER_TOKEN, "oauth_token_secret": USER_SECRET
            }
        )
        grouplist = splitwiseobj.getGroups()
        currentUser = splitwiseobj.getCurrentUser()
        for group in grouplist:
            debtList = group.getSimplifiedDebts()
            print "In Group " + group.getName()
            for debts in debtList:
                if debts.getFromUser() != currentUser.id:
                    continue
                user = splitwiseobj.getUser(debts.getToUser())
                print user.getFirstName() + " " + str(debts.getCurrencyCode()) + " " + debts.getAmount()
            print "================================="


class UnknownProcessor(BaseProcessor):
    MSG1 = "Sorry, I didn't understand that"
    MSG2 = "Apologies, I missed that"

    def __init__(self):
        self.message = []
        self.message.append(self.MSG1)
        self.message.append(self.MSG2)

    def process(self, input):
        return random.choice(self.message)
