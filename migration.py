"""
Migration support scripts to help facilitate loading many
accounts from a Microsoft Money export, based on the
instructions at
https://infinitekind.zendesk.com/hc/en-us/articles/200684598-Moving-from-MS-Money-to-Moneydance
"""

from __future__ import print_function, unicode_literals

import os
import json
import datetime
import calendar
import re
import io
import itertools

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
	ts = model.TransactionSet(moneydance.getCurrentAccountBook())
	txns = ts.getAllTxns()
	txns.removeAllTxns()
	root = moneydance.getCurrentAccount()
	for account in root.getSubAccounts():
		account.deleteItem()


def parse_date(date_str):
	"""
	Given a simple date string, parse it into a timestamp
	suitable for setCreationDate.
	"""
	date = datetime.datetime(*map(int, date_str.split('-')))
	seconds = calendar.timegm(date.utctimetuple())
	timestamp = seconds*long(1000)
	return timestamp


def create_account(details):
	"""
	Given a dictionary of account details, create an account
	corresponding to those details and yield said account. If
	the account is an investment account, also yield a corresponding
	cash account.
	"""
	root = moneydance.getCurrentAccount()
	book = moneydance.getCurrentAccountBook()
	type_name = details.get('type', 'bank')
	type_ = getattr(model.Account.AccountType, type_name.upper())
	account = root.makeAccount(book, type_, root)
	account.setAccountName(details['name'])
	account.setBankName(details['bank'])
	if 'number' in details:
		account.setBankAccountNumber(details['number'])
	if 'bank id' in details:
		account.setOFXBankID(details['bank id'])
	if 'currency' in details:
		idstr = details['currency']
		currency = book.getCurrencies().getCurrencyByIDString(idstr)
		account.setCurrencyType(currency)
	if 'create date' in details:
		account.setCreationDate(parse_date(details['create date']))
	yield account
	if type_ == model.Account.AccountType.INVESTMENT:
		print("Creating cash account for", account.getAccountName())
		# create the cash account
		details['name'] += ' (Cash)'
		details.pop('type')
		for acct in create_account(details):
			yield acct


def import_transactions(account):
	"""
	Given an account, import the transactions for that account
	from a file of the same account name in this directory.
	"""
	root = moneydance.getCurrentAccount()
	book = moneydance.getCurrentAccountBook()
	transactions = os.path.join(here, account.getAccountName()) + '.qif'
	transactions = correct_encoding(transactions)
	correct_opening_balance(transactions, account.getAccountName())
	file = java.io.File(transactions)
	date_format = Common.QIF_FORMAT_DDMMYY
	dec = '.'
	currency = account.getCurrencyType()
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


def correct_opening_balance(qif_file, account_name):
	"""
	QIF files from Money have a "Opening Balance" transaction whose
	category is a transfer to the same account. This transaction when
	imported into Moneydance creates a duplicate account. Remove
	that category such that the transaction appears with no
	category.
	"""
	with io.open(qif_file, encoding='utf-8') as f:
		data = f.read()
	name = re.escape('[' + account_name + ']')
	pat = re.compile('^L' + name + r'\n', re.MULTILINE)
	patched_data = pat.sub('', data)
	if patched_data == data:
		print("No opening balanace detected for", account_name)
	with io.open(qif_file, 'w', encoding='utf-8') as f:
		f.write(patched_data)


def correct_encoding(qif_file):
	"""
	Money saves the file as Latin-1 encoding, which is a terrible
	encoding, and not recognized by Moneydance. Switch to UTF-8.
	Keep the old file around for reference and return a new filename.
	"""
	out_file = qif_file.replace('.qif', ' (edit).qif')
	with io.open(qif_file, encoding='latin-1') as in_:
		with io.open(out_file, 'w', encoding='utf-8') as out:
			out.writelines(in_.readlines())
	return out_file


# from Python 2.7 docs
def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)


def run(moneydance=None):
	"""
	Run the import process across all accounts in accounts.json.
	"""
	if moneydance:
		init(moneydance)
	delete_all_accounts()
	account_meta = os.path.join(here, 'accounts.json')
	with open(account_meta) as meta:
		accounts_meta = json.load(meta)
	print("Migrating", len(accounts_meta), "accounts")
	# first, create all accounts
	accounts = list(flatten(map(create_account, accounts_meta)))
	# then import transactions into the created accounts
	for account in accounts:
		import_transactions(account)
