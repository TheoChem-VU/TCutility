from tcutility.job import ADFJob
from tcutility import results, geometry, molecule, slurm
import pytest
import numpy as np


@pytest.fixture(scope='session')
def run_jobs():
    jobs = results.Result()

    with ADFJob(overwrite=True) as jobs.SP_job:
        jobs.SP_job.molecule('../fixtures/xyz/ethanol.xyz')
        jobs.SP_job.rundir = 'calculations'
        jobs.SP_job.name = 'ethanol_SP'
        jobs.SP_job.sbatch(p='tc', n=16)

    with ADFJob(overwrite=True) as jobs.GO_job:
        mol = molecule.load('../fixtures/xyz/ethanol.xyz')
        np.random.seed(1)
        arr = mol.as_array() + (np.random.rand(*mol.as_array().shape) - .5) * .2
        mol.from_array(arr)

        jobs.GO_job.molecule(mol)

        jobs.GO_job.rundir = 'calculations'
        jobs.GO_job.name = 'ethanol_GO'
        jobs.GO_job.sbatch(p='tc', n=16)

        jobs.GO_job.optimization()

    with ADFJob(overwrite=True) as jobs.TS_job:
        mol = molecule.load('../fixtures/xyz/TS.xyz')
        jobs.TS_job.molecule(mol)

        jobs.TS_job.rundir = 'calculations'
        jobs.TS_job.name = 'SN2_TS'
        jobs.TS_job.sbatch(p='tc', n=32)

        jobs.TS_job.transition_state(distances=[mol.flags.TSRC1, mol.flags.TSRC2])
        jobs.TS_job.functional('OLYP')
        jobs.TS_job.charge(-1)

    # wait for all jobs to finish running
    for job in jobs.values():
        slurm.wait_for_job(job.slurm_job_id)

    return jobs


@pytest.fixture(scope='session')
def SP_job_res(run_jobs):
    return results.read(run_jobs.SP_job.workdir)


@pytest.fixture(scope='session')
def GO_job_res(run_jobs):
    return results.read(run_jobs.GO_job.workdir)


@pytest.fixture(scope='session')
def TS_job_res(run_jobs):
    return results.read(run_jobs.TS_job.workdir)


def test_SP_job_slurmid(run_jobs):
    assert run_jobs.SP_job.slurm_job_id is not None


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
