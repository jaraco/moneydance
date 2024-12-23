import itertools

from com.infinitekind.moneydance import model

import demo
from __main__ import moneydance


def _print_transactions(limit=10):
    # get the default environment variables, set by Moneydance
    print("The Moneydance app controller: %s" % (moneydance))
    print("The current data set: %s" % (moneydance.getCurrentAccountBook()))
    print("The UI: %s" % (moneydance.ui))

    txns = model.TransactionSet(moneydance.getCurrentAccountBook())

    for txn in itertools.islice(txns.getAllTxns(), limit):
        print(
            "transaction: date %u: description: %s for amount %s"
            % (
                txn.getDateInt(),
                txn.getDescription(),
                txn.getAccount().getCurrencyType().formatFancy(txn.getValue(), "."),
            )
        )


def acct(name="Amazon Purchases"):
    return moneydance.getCurrentAccount().getAccountByName(name)


def get_transactions(account):
    book = moneydance.getCurrentAccountBook()
    return book.getTransactionSet().getTransactionsForAccount(account)


def print_transactions(account, limit=10):
    for txn in itertools.islice(get_transactions(account), limit):
        print(txn)
