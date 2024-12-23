from __future__ import print_function, unicode_literals

import datetime

from __main__ import moneydance
from com.infinitekind.moneydance import model

__metaclass__ = type

# suppress linter warning for Py3
if False:
    long = int


def create_transaction(account):
    book = moneydance.getCurrentAccountBook()
    txn = model.ParentTxn(book)
    txn.date = txn.taxDate = int(datetime.date.today().strftime("%Y%m%d"))
    txn.account = account
    spl = model.SplitTxn(txn)
    spl.setAmount(long(1))
    txn.addSplit(spl)
    txn.syncItem()
    return txn, spl
