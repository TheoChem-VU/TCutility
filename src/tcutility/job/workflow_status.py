from tcutility.job import workflow_db
from tcutility import cache
import os
import sys

@cache
def _detect_hsh():
	file = os.getcwd()
	all_data = workflow_db.read_all()
	for hsh, data in all_data.items():
		if 'run_directory' not in data:
			continue
			
		if file.startswith(data['run_directory']):
			return hsh


def stage(message):
	hsh = _detect_hsh()
	sys.stdout.flush()

	workflow_db.update(hsh, stage=message)
