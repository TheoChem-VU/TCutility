from tcutility.job import ADFJob
from tcutility import results, geometry, molecule
import pytest
import numpy as np


@pytest.fixture(scope='session')
def SP_job():
    with ADFJob(wait_for_finish=True, overwrite=False) as job:
        job.molecule('../fixtures/xyz/ethanol.xyz')
        job.rundir = 'calculations'
        job.name = 'ethanol_SP'
        job.sbatch(p='tc', n=16)

    return job


@pytest.fixture(scope='session')
def SP_job_res(SP_job):
    return results.read(SP_job.workdir)


@pytest.fixture(scope='session')
def GO_job():
    with ADFJob(wait_for_finish=True, overwrite=False) as job:
        mol = molecule.load('../fixtures/xyz/ethanol.xyz')
        np.random.seed(1)
        arr = mol.as_array() + (np.random.rand(*mol.as_array().shape) - .5) * .3
        mol.from_array(arr)

        job.molecule(mol)

        job.rundir = 'calculations'
        job.name = 'ethanol_GO'
        job.sbatch(p='tc', n=16)

        job.optimization()

    return job


@pytest.fixture(scope='session')
def GO_job_res(GO_job):
    return results.read(GO_job.workdir)


@pytest.fixture(scope='session')
def TS_job():
    with ADFJob(wait_for_finish=True, overwrite=False) as job:
        mol = molecule.load('../fixtures/xyz/TS.xyz')
        job.molecule(mol)

        job.rundir = 'calculations'
        job.name = 'SN2_TS'
        job.sbatch(p='tc', n=32)

        job.transition_state(distances=[mol.flags.TSRC1, mol.flags.TSRC2])
        job.functional('OLYP')
        job.charge(-1)

    return job


@pytest.fixture(scope='session')
def TS_job_res(TS_job):
    return results.read(TS_job.workdir)


def test_SP_job_slurmid(SP_job):
    assert SP_job.slurm_job_id is not None


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
    assert round(rmsd, 2) == 0


def test_GO_job_imfreq(GO_job_res):
    assert GO_job_res.properties.vibrations.number_of_imag_modes == 0


def test_TS_job_status(TS_job_res):
    assert TS_job_res.status.name == 'SUCCESS'


def test_TS_job_energy(TS_job_res):
    assert round(TS_job_res.properties.energy.bond, 2) == -582.63


def test_TS_job_rmsd(TS_job_res):
    rmsd = geometry.RMSD(TS_job_res.molecule.output, molecule.load('../fixtures/xyz/TS.xyz'))
    assert round(rmsd, 2) == 0


def test_TS_job_imfreq(TS_job_res):
    assert TS_job_res.properties.vibrations.number_of_imag_modes == 1


if __name__ == '__main__':
    pytest.main()
