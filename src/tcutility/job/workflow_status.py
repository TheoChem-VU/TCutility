from tcutility.job import workflow_db
from tcutility import cache
import os
import sys

@cache
def _detect_hsh():
	file = os.getcwd()
	all_data = workflow_db.read_all()
	for hsh, data in all_data.items():
		if hsh in file:
			return hsh


def stage(message):
	hsh = _detect_hsh()
	# if the job is not managed by tcutility we simply print the message
	if hsh is None:
		print(message)
		return

	# otherwise update the workflow DB
	workflow_db.update(hsh, stage=message)
