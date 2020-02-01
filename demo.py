import itertools

from com.infinitekind.moneydance import model

from __main__ import moneydance


def print_transactions(limit=10):
    # get the default environment variables, set by Moneydance
    print("The Moneydance app controller: %s" % (moneydance))
    print("The current data set: %s" % (moneydance.getCurrentAccountBook()))
    print("The UI: %s" % (moneydance.ui))

    txns = model.TransactionSet(moneydance.getCurrentAccountBook())

    for txn in itertools.islice(txns.getAllTxns(), limit):
        print(
            "transaction: date %u: description: %s for amount %s" % (
                txn.getDateInt(),
                txn.getDescription(),
                txn.getAccount().getCurrencyType().formatFancy(
                    txn.getValue(), '.'),
            )
        )


def print_transactions_for_account(account_name):
    root = moneydance.getCurrentAccount()
    book = moneydance.getCurrentAccountBook()

    account = root.getAccountByName(account_name)
    assert account

    txns = book.getTransactionSet().getTransactionsForAccount(account)
    for txn in txns:
        print(txn)


print_transactions_for_account('Amazon Purchases')
