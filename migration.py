import os
import json
import datetime
import calendar

import com.infinitekind.moneydance.model as model
import com.moneydance.apps.md.controller.Common as Common
import java.io

moneydance = None
here = os.path.dirname(__file__)


def init(moneydance):
	globals().update(moneydance=moneydance)


def delete_all_accounts():
	"""
	Delete all accounts from the file, allowing for a fresh import.
	"""
	txns = model.TransactionSet(moneydance.getCurrentAccountBook()).getAllTxns()
	txns.removeAllTxns()
	root = moneydance.getCurrentAccount()
	for account in root.getSubAccounts():
		account.deleteItem()


def parse_date(date_str):
	date = datetime.datetime(*map(int, date_str.split('-')))
	seconds = calendar.timegm(date.utctimetuple())
	timestamp = seconds*long(1000)
	return timestamp


def import_account(details):
	root = moneydance.getCurrentAccount()
	book = moneydance.getCurrentAccountBook()
	account = root.makeAccount(book, model.Account.AccountType.BANK, root)
	account.setAccountName(details['name'])
	account.setBankName(details['bank'])
	account.setBankAccountNumber(details['number'])
	account.setOFXBankID(details['bank id'])
	account.setCreationDate(parse_date(details['create date']))
	import_transactions(account)


def import_transactions(account):
	root = moneydance.getCurrentAccount()
	book = moneydance.getCurrentAccountBook()
	transactions = os.path.join(here, account.getAccountName()) + '.qif'
	file = java.io.File(transactions)
	date_format = Common.QIF_FORMAT_DDMMYY
	dec = '.'
	currency = book.getCurrencies().getBaseType()
	import_mode = Common.QIF_MODE_TRANSFER
	accts_only = False
	moneydance.importQIFIntoAccount(
		book,
		file,
		date_format,
		dec,
		currency,
		account,
		import_mode,
		accts_only,
	)

def run(moneydance=None):
	if moneydance:
		init(moneydance)
	delete_all_accounts()
	account_meta = os.path.join(here, 'accounts.json')
	with open(account_meta) as meta:
		accounts = json.load(meta)
	for account in accounts:
		import_account(account)
