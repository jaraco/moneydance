# -*- coding: utf-8

"""
Migration support scripts to help facilitate loading many
accounts from a Microsoft Money export, based on the
instructions at
https://infinitekind.zendesk.com/hc/en-us/articles/200684598-Moving-from-MS-Money-to-Moneydance

In addition to those instructions, here are some other caveats:

 - Rename any cash accounts to be "Investment Account (Cash)"
 - If the account name has any special characters, replace them
   with a dash in the saved file.
"""

from __future__ import print_function, unicode_literals

import os
import json
import datetime
import calendar
import re
import io
import itertools
import glob

import com.infinitekind.moneydance.model as model
import com.moneydance.apps.md.controller.Common as Common
import java.io

moneydance = None
here = os.path.dirname(__file__)

# suppress linter warning for Py3
if False:
	long = int

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


def get_account_by_name(name):
	root = moneydance.getCurrentAccountBook()
	root_acct = root.getRootAccount()
	return root_acct.getAccountByName(name)


def txns_for(account):
	root = moneydance.getCurrentAccountBook()
	return root.getTransactionSet().getTransactionsForAccount(account)


def first_txn_date(account):
	all_txns = txns_for(account)
	by_date = lambda txn: txn.getDateInt()
	dates = map(by_date, all_txns)
	return min(dates)


def ts_from_date_int(date_int):
	"""
	Take a string of the form YYYYMMDD and convert it to a
	timestamp.
	"""
	year = date_int // 10000
	month = (date_int % 10000) // 100
	day = (date_int % 100)
	date = datetime.datetime(year, month, day)
	seconds = calendar.timegm(date.utctimetuple())
	timestamp = seconds*long(1000)
	return timestamp


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
	type_name = details.get('type', 'bank').replace(' ', '_')
	type_ = getattr(model.Account.AccountType, type_name.upper())
	account = root.makeAccount(book, type_, root)
	account.setAccountName(details['name'])
	if 'bank' in details:
		account.setBankName(details['bank'])
	if 'number' in details:
		account.setBankAccountNumber(details['number'])
	if 'bank id' in details:
		account.setOFXBankID(details['bank id'])
	if 'currency' in details:
		idstr = details['currency']
		currency = book.getCurrencies().getCurrencyByIDString(idstr)
		account.setCurrencyType(currency)
	yield account
	if type_ == model.Account.AccountType.INVESTMENT:
		print("Creating cash account for", account.getAccountName())
		# create the cash account
		details['name'] += ' (Cash)'
		details.pop('type')
		for acct in create_account(details):
			yield acct


def safe(account_name):
	"""
	Create a filesystem-safe name from an account name.
	"""
	return account_name.replace('*', '-')


def import_transactions(account):
	"""
	Given an account, import the transactions for that account
	from a file of the same account name in this directory.
	"""
	book = moneydance.getCurrentAccountBook()
	acct_name = account.getAccountName()
	transactions = os.path.join(here, safe(acct_name)) + '.qif'
	if account.getAccountType() == model.Account.AccountType.LOAN:
		print("Cannot import transactions for loan account", acct_name)
		return
	if not os.path.isfile(transactions):
		print("No transactions found for", acct_name)
		return
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
	os.remove(transactions)

	account.setCreationDate(ts_from_date_int(first_txn_date(account)))


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
	out_file = qif_file.replace('.qif', '.uqif')
	with io.open(qif_file, encoding='latin-1') as in_:
		with io.open(out_file, 'w', encoding='utf-8') as out:
			out.writelines(in_.readlines())
	return out_file


# from Python 2.7 docs
def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


def move_cash(accounts):
	"move cash transactions into investment accounts"
	inv_pairs = filter(is_inv_pair, pairwise(accounts))
	list(itertools.starmap(merge_inv_cash, inv_pairs))


def is_inv_pair(acct_pair):
	acct, _ = acct_pair
	return acct.getAccountType() == model.Account.AccountType.INVESTMENT


def merge_inv_cash(inv_acct, cash_acct):
	"""
	Given an investment account and its sister cash account,
	move the cash transactions into the investment account.
	"""
	cash_txns = (
		txn
		for txn in txns_for(cash_acct)
		if txn.getAccount() == cash_acct
		and not txn.isTransferTo(inv_acct)
	)
	for txn in cash_txns:
		txn.setAccount(inv_acct)
		txn.getParentTxn().syncItem()
	cash_acct.deleteItem()


def create_currencies():
	"""
	Create bitcoin currency and others that aren't supplied out
	of the box.
	"""
	specs = load_metadata().get('currencies', [])
	for spec in specs:
		_create_currency(**spec)


def _create_currency(code, name, rate=1, decimal_places=2, prefix=None, suffix=None):
	"""
	rate is the value of one unit of the default currency in this new currency
	"""
	table = moneydance.getCurrentAccountBook().getCurrencies()
	currency = model.CurrencyType(table)
	currency.setCurrencyType(model.CurrencyType.Type.CURRENCY)
	currency.setIDString(code)
	currency.setName(name)
	# important to always set decimal places. Otherwise, moneydance
	# will set the decimal places to 2 after setting the rate, which
	# will break the rate.
	currency.setDecimalPlaces(decimal_places)
	if prefix:
		currency.setPrefix(prefix)
	if suffix:
		currency.setSuffix(suffix)
	# important that you set the rate after setting decimal places;
	# otherwise, setting decimal places will adjust the rate.
	currency.setUserRate(rate)
	currency.syncItem()


def load_metadata():
	filename = os.path.join(here, 'migration.json')
	with open(filename) as meta:
		return json.load(meta)


def load_accounts_meta():
	accounts = load_metadata()['accounts']
	return accounts + infer_accounts(accounts)


def infer_accounts(declared_accounts):
	"""
	Discover any accounts that were exported but not declared and add them
	"""
	known_names = {safe(account['name']) for account in declared_accounts}
	exports = glob.glob(os.path.join(here, '*.qif'))
	export_names = {
		root
		for root, ext in map(os.path.splitext, map(os.path.basename, exports))
		if not root.endswith(' (Cash)')
	}
	new_names = export_names - known_names
	if not new_names:
		raise ValueError()
	msg = "Assuming bank for these detected accounts: ", ', '.join(new_names)
	if new_names:
		print(msg)
	return [dict(name=name) for name in new_names]


def find_duplicate_transactions(account):
	"""
	For a given foreign transaction account, find matching
	transaction pairs.
	"""
	local_txns = (
		txn for txn in
		txns_for(account).iterator()
		if isinstance(txn, model.ParentTxn)
	)
	remote_txns = (
		txn
		for txn in txns_for(account).iterator()
		if not isinstance(txn, model.ParentTxn)
	)
	pairs = itertools.product(local_txns, remote_txns)

	for local, remote in pairs:
		match = (
			local.getMemo() == remote.getOtherTxn(0).getMemo()
			and
			local.getDescription() == remote.getDescription()
			and
			local.getDateInt() == remote.getDateInt()
		)
		if match:
			yield local, remote


def run(moneydance=None):
	"""
	Run the import process across all accounts in accounts.json.
	"""
	if moneydance:
		init(moneydance)

	create_currencies()

	start = datetime.datetime.utcnow()
	delete_all_accounts()
	end = datetime.datetime.utcnow()
	print("Deleted existing accounts in", end-start)

	try:
		accounts_meta = load_accounts_meta()
	except ValueError as err:
		print("Error loading accounts", err)
		return

	print("Migrating", len(accounts_meta), "accounts")
	# first, create all accounts
	accounts = list(flatten(map(create_account, accounts_meta)))
	# then import transactions into the created accounts
	for account in accounts:
		import_transactions(account)

	move_cash(accounts)

	end = datetime.datetime.utcnow()
	print("Completed in", end-start)
