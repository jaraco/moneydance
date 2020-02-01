from __future__ import print_function, unicode_literals

import datetime

from __main__ import moneydance
from com.infinitekind.moneydance import model

__metaclass__ = type


def create_transaction(account_name):
    root = moneydance.getCurrentAccount()
    book = moneydance.getCurrentAccountBook()
    txn = model.ParentTxn(book)
    txn.date = int(datetime.date.today().strftime('%Y%m%d'))
    account = root.getAccountByName(account_name)
    txn.account = account
    spl = model.SplitTxn(txn)
    spl.setAmount(1)
    txn.syncItem()
