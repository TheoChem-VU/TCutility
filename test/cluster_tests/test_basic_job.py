from tcutility.job import ADFJob
from tcutility import results, geometry, molecule
import pytest
import numpy as np


@pytest.fixture(scope='session')
def SP_job_res():
	with ADFJob(wait_for_finish=True, overwrite=False) as job:
		job.molecule('../fixtures/xyz/ethanol.xyz')
		job.rundir = 'calculations'
		job.name = 'ethanol_SP'

	return results.read(job.workdir)

@pytest.fixture(scope='session')
def GO_job_res():
	with ADFJob(wait_for_finish=True, overwrite=False) as job:
		mol = molecule.load('../fixtures/xyz/ethanol.xyz')
		np.random.seed(1)
		arr = mol.as_array() + (np.random.rand(*mol.as_array().shape) - .5) * .3
		mol.from_array(arr)

		job.molecule(mol)

		job.rundir = 'calculations'
		job.name = 'ethanol_GO'

		job.optimization()

	return results.read(job.workdir)

@pytest.fixture(scope='session')
def TS_job_res():
	with ADFJob(wait_for_finish=True, overwrite=True) as job:
		mol = molecule.load('../fixtures/xyz/TS.xyz')
		job.molecule(mol)

		job.rundir = 'calculations'
		job.name = 'radical_addition_TS'

		job.transition_state(distances=[mol.flags.TSRC + [1]])
		job.functional('BLYP-D3(BJ)')
		job.spin_polarization(1)

	return results.read(job.workdir)


def test_SP_job_status(SP_job_res):
	assert SP_job_res.status.name == 'SUCCESS'

def test_SP_job_energy(SP_job_res):
	assert round(SP_job_res.properties.energy.bond, 2) == -1137.70

def test_GO_job_status(GO_job_res):
	assert GO_job_res.status.name == 'SUCCESS'

def test_GO_job_energy(GO_job_res):
	assert round(GO_job_res.properties.energy.bond, 2) == -1137.70

def test_GO_job_rmsd(GO_job_res):
	rmsd = geometry.RMSD(GO_job_res.molecule.output, molecule.load('../fixtures/xyz/ethanol.xyz'))
	assert round(rmsd, 3) == 0

def test_GO_job_imfreq(GO_job_res):
	assert GO_job_res.properties.vibrations.number_of_imag_modes == 0

def test_TS_job_status(TS_job_res):
	assert TS_job_res.status.name == 'SUCCESS'

def test_TS_job_energy(TS_job_res):
	assert round(TS_job_res.properties.energy.bond, 2) == -1137.70

def test_TS_job_rmsd(TS_job_res):
	rmsd = geometry.RMSD(TS_job_res.molecule.output, molecule.load('../fixtures/xyz/ethanol.xyz'))
	assert round(rmsd, 3) == 0

def test_TS_job_imfreq(TS_job_res):
	assert TS_job_res.properties.vibrations.number_of_imag_modes == 1


if __name__ == '__main__':
	pytest.main()
