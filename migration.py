from __future__ import print_function, unicode_literals

import os
import json
import datetime
import calendar
import re
import io

import com.infinitekind.moneydance.model as model
import com.moneydance.apps.md.controller.Common as Common
import java.io

moneydance = None
here = os.path.dirname(__file__)

# https://infinitekind-public.slack.com/archives/moneydance/p1443904386000011


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
	corresponding to those details and return said account.
	"""
	root = moneydance.getCurrentAccount()
	book = moneydance.getCurrentAccountBook()
	account = root.makeAccount(book, model.Account.AccountType.BANK, root)
	account.setAccountName(details['name'])
	account.setBankName(details['bank'])
	account.setBankAccountNumber(details['number'])
	if 'bank id' in details:
		account.setOFXBankID(details['bank id'])
	if 'currency' in details:
		idstr = details['currency']
		currency = book.getCurrencies().getCurrencyByIDString(idstr)
		account.setCurrencyType(currency)
	account.setCreationDate(parse_date(details['create date']))
	return account


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
	pat = re.compile('^L\[' + account_name + r'\]\n', re.MULTILINE)
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
	# first, create all accounts
	accounts = list(map(create_account, accounts_meta))
	# then import transactions into the created accounts
	for account in accounts:
		import_transactions(account)
