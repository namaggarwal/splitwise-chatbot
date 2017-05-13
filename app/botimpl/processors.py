from app.bot import BaseProcessor, BotProcessorFactory
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser

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
class SplitwiseBotProcessorFactory(BotProcessorFactory):

    def __init__(self):
        pass

    def getProcessor(self, action):
        if action == 'transaction':
            return TransactionProcessor()


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
                expenseuser = self.getExpenseUser(friend,owed,paid)
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
            owed = amount/2.0
        return paid, owed

    def getExpenseUser(self, friend, paid, owed):
        user = ExpenseUser()
        user.setId(friend.getId())
        user.setPaidShare(str(paid))
        user.setOwedShare(str(owed))
        return user
