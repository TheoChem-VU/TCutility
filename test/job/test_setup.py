from tcutility import job as tcjob
import os
j = os.path.join
s = os.path.split


def test_ADFJob():
	with tcjob.ADFJob(delete_on_finish=True, test_mode=True) as job:
		job.name = '.ADFJob'

def test_ADFFragmentJob():
	with tcjob.ADFFragmentJob(delete_on_finish=True, test_mode=True) as job:
		job.name = '.ADFFragmentJob'
		job.molecule(j(s(s(__file__)[0])[0], "fixtures", "xyz", "NaCl_homolytic.xyz"))


if __name__ == '__main__':
	import pytest

	pytest.main()
