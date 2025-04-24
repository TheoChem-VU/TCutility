import os
import fcntl


DBPATH = os.path.split(__file__)[0] + '/.workflow.txt'
if not os.path.exists(DBPATH):
	with open(DBPATH, 'w+'):
		...


def db_readlines():
	with open(DBPATH) as db:
		fcntl.flock(db.fileno(), fcntl.LOCK_EX)
		lines = db.readlines()
		fcntl.flock(db.fileno(), fcntl.LOCK_UN)
	return lines


def get_status(hsh):
	'''
	Get the status of a workflow with specific args and kwargs.
	'''
	lines = db_readlines()
	data = {}
	for line in lines:
		_hsh, status = line.split(',')
		data[_hsh.strip()] = status.strip()

	return data.get(hsh, 'UNKNOWN')


def can_skip(hsh):
	'''
	Checks if a workflow with specific args and kwargs has finished.
	'''
	return get_status(hsh) in ['SUCCESS', 'RUNNING', 'FAILED']


def set_status(hsh, status):
	'''
	Checks if a workflow with specific args and kwargs has finished.
	'''
	with open(DBPATH, 'a') as db:
		fcntl.flock(db.fileno(), fcntl.LOCK_EX)
		
		db.write(f'{hsh}, {status}\n')

		fcntl.flock(db.fileno(), fcntl.LOCK_UN)


def set_running(hsh):
	'''
	Checks if a workflow with specific args and kwargs has finished.
	'''
	set_status(hsh, 'RUNNING')


def set_finished(hsh):
	'''
	Checks if a workflow with specific args and kwargs has finished.
	'''
	set_status(hsh, 'SUCCESS')


def set_failed(hsh):
	'''
	Checks if a workflow with specific args and kwargs has finished.
	'''
	set_status(hsh, 'FAILED')
