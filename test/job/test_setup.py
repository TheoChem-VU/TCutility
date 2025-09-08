import os

from tcutility.job import adf

j = os.path.join
s = os.path.split


def test_ADFJob():
    with adf.ADFJob(delete_on_finish=True, test_mode=True) as job:
        job.name = ".ADFJob"


# TODO The job makes a tmp folder which is not deleted for some reason


def test_ADFFragmentJob():
    with adf.ADFFragmentJob(delete_on_finish=True, test_mode=True) as job:
        job.name = ".ADFFragmentJob"
        job.molecule(j(s(s(__file__)[0])[0], "fixtures", "xyz", "NaCl_homolytic.xyz"))


if __name__ == "__main__":
    test_ADFFragmentJob()
