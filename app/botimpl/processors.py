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
        elif action == 'music':
            return MusicProcessor()
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
        split = 'paid'
        amount = 0
        name = ''
        description = ''


        if 'result' in input:
            result = input['result']
            if 'parameters' in result:
                parameters = result['parameters']
                if not SPLIT in parameters or len(parameters[SPLIT]) == 0:
                    return "Please enter whether you paid or owe"
                split = str(parameters.get(SPLIT, PAID))
                if not AMOUNT in parameters or len(parameters[AMOUNT]) == 0:
                    return self.amountError(split)
                if not NAME in parameters or len(parameters[NAME]) == 0:
                    return "Please enter the name of the person"

                name = str(parameters.get(NAME))
                amount = str(parameters[AMOUNT])
                description = str(parameters.get(DESC))


        expense = Expense()
        expense.setCost(amount)

        mode = split.lower()

        if description =="" or len(description)==0:
            description = BOT

        expense.setDescription(description)

        # current user
        paid, owed = self.getDistribution(mode, amount)
        cuser = self.getExpenseUser(currentUser, paid, owed)
        userlist.append(cuser)

        match = False
        for friend in friendslist:
            if friend.getFirstName().lower() == name.lower():
                expenseuser = self.getExpenseUser(friend, owed, paid)
                match = True
                if mode != PAID and mode != OWE:
                    expenseuser.setPaidShare(str(0))
                    expenseuser.setOwedShare(str(owed))

                output += friend.getFirstName()
                userlist.append(expenseuser)
                break

        if not match:
            return "You don't have any friend named '"+ name+"'"


        expense.setUsers(userlist)
        expense = splitwiseobj.createExpense(expense)
        if expense.getId() is None or len(str(expense.getId()))==0:
            return "Oops Sorry ! Some error has Occured"
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

    def getAmountError(self, split):
        errors = []
        E1 = "Please enter the amount"
        E2 = "I didn't find the amount you "+split
        E3 = "how much amount did you "+split
        errors.append(E3,E2,E1)
        return random.choice(errors)


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
            if not expense.getDeletedAt() is None:
                continue
            owedshare = self.getOwedShare(expense.getUsers(), currentuser.getId())
            if not owedshare is None:
                code = expense.getCurrencyCode()
                if code in dc:
                    dc[code] += float(owedshare)
                else:
                    dc[code] = float(owedshare)
        response = "Showing expense for Last " + str(days) + SPACE + self.DAYS + "\n"
        output = currentuser.getDefaultCurrency() + " 0.0"
        for key, value in dc.iteritems():
            output = str(key) + SPACE + str(value) + "\n"

        return response + output

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
        if 'result' in input:
            result = input['result']
            if 'parameters' in result:
                parameters = result['parameters']
                days = int(parameters[self.DAYS])
        if days ==0:
            days = 7

        date = datetime.now() - timedelta(days=days)
        limit = 1000

        allExpense = splitwiseobj.getExpenses(limit=limit, dated_after=date)
        agg = AggregationProcessor()
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
            dateob = dateob.strftime('%Y-%m-%d')
            #output += dateob + ": "
            output = expense.getDescription()+SPACE+"="+SPACE+expense.getCurrencyCode() + SPACE + str(owedshare)  + "\n"
            if dateob in outputdc:
                outputdc[dateob] += output
            else:
                outputdc[dateob] = output
        output = EXPENSE_SUMMARY + SPACE+ FOR + SPACE + "last " + str(days) + SPACE + self.DAYS + "\n"
        outputdc = sorted(outputdc.items())
        for key,value in outputdc:
            output += "\nDate: " +str(key) + "\n"
            output += value

        totalresp = "\nTotal expenditure is "+currentuser.getDefaultCurrency()+SPACE + str(totalOwe)
        output += str(totalresp)
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
    MSG2 = "Apologies, I missed that, could you please repeat"

    def __init__(self):
        self.message = []
        self.message.append(self.MSG1)
        self.message.append(self.MSG2)

    def process(self, input):
        return random.choice(self.message)

class MusicProcessor(BaseProcessor):

    def __init__(self):
        pass

    def process(self,input):
        result = {}
        artist = ''
        if "result" in input:
            result = input["result"]
            artist = result["parameters"]["artist"]

        return "You were referring to "+artist

