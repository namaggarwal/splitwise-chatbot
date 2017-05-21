
class BotConstants(object):

    # GENERAL CONSTANTS
    DESCRIPTION = "description"
    SPLIT = "split"
    PAID = "paid"
    OWE = "owe"
    AMOUNT = 'amount'
    CURRENCY = "currency"
    EQUALLY = "equally"
    RESULT = "result"
    PARAMETERS = "parameters"
    LIMIT = "limit"
    DAYS = "days"
    SPACE = " "
    FOR = "for"
    DATE = "Date:"
    LINEBREAK = "\n"
    USER_ID = "user_id"
    QUESTION = "?"
    FROM_BOT = "From Bot"
    # Transaction Processor
    NAME = "name"
    GROUP = "group"

    WANT_TO_SPLIT = "want to split "
    NEW_EXPENSE_OUTPUT = "New Expense has been added between You and "

    # Aggregation Processor
    ZERO = "0.0"

    # List Processor
    EQUAL = "="

    LOGIN_SUCCESS = "You are logged in."
    In_GROUP = "In Group"
    HELP = "help"







class ErrorMessages(object):

    UNKNOWN = [
        "Sorry, I didn't understand that",
        "Can your frame that in other way",
        "I don't know that yet",
        "Sorry, I can't answer that now"
    ]

    NAME = "Please enter the name of the person"
    SPLIT = "Please enter whether you paid or owe"
    WRONG_SPLIT = "Wrong value of Split, please use either 'paid', 'owe' or 'equally'"
    GENERAL = "Sorry, some error has occured. Please try again. "
    NO_FRIEND = "You don't have any friend named {name}"
    GROUP= "Sorry, the group you have mentioned doesn't exist"

