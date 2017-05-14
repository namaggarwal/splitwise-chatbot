from app.bot import BaseProcessor, BotProcessorFactory
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from splitwise.group import Group
from splitwise.debt import Debt
import random
from datetime import datetime, timedelta

USER_TOKEN = ''
USER_SECRET = ''

APP_KEY = ''
APP_SECRET = ''

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


class TransactionProcessor(BaseProcessor):
    def __init__(self):
        pass

    def process(self, input):
        output = OUTPUT
        splitwiseobj = Splitwise(APP_KEY, APP_SECRET)
        splitwiseobj.setAccessToken(
            {
                "oauth_token": USER_TOKEN, "oauth_token_secret": USER_SECRET
            }
        )
        currentUser = splitwiseobj.getCurrentUser()
        friendslist = splitwiseobj.getFriends()

        userlist = []
        amount = input.get(AMOUNT)

        expense = Expense()
        expense.setCost(amount)

        mode = input.get(SPLIT).lower()

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
            if friend.getFirstName().lower() == input.get(NAME).lower():
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
        splitwiseobj = Splitwise(APP_KEY, APP_SECRET)
        splitwiseobj.setAccessToken(
            {
                "oauth_token": USER_TOKEN, "oauth_token_secret": USER_SECRET
            }
        )
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
        for expense in allExpense:
            date = expense.getDate()
            dateob = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            output += dateob.strftime('%Y-%m-%d') + ": "
            output += YOU + SPACE + OWE + SPACE + expense.getCurrencyCode() + SPACE
            owedshare = self.getOwedShare(expense.getUsers(), currentuser.getId())
            if owedshare is None:
                owedshare=0.0
            output += str(owedshare) + SPACE+ FOR + SPACE + expense.getDescription() + "\n"

        return output

    def getOwedShare(self, userList, currentUserId):
        for expenseuser in userList:
            if expenseuser.getId() == currentUserId:
                return expenseuser.getOwedShare()


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
