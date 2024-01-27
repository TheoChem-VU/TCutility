import subprocess as sp
from tcutility import results, log, cache
import time
import os


@cache.cache
def has_slurm() -> bool:
    '''
    Function to check if the current platform uses slurm. 

    Returns:
        Whether slurm is available on this platform.
    '''
    try:
        # we do not want this function to print anything when it does not find sbatch
        with open(os.devnull, 'wb') as devnull:
            sp.check_output(['which', 'sbatch'], stderr=devnull).decode()
        # if it runs without error, we have access to slurm
        return True
    # if an error is raised we do not have slurm
    except sp.CalledProcessError:
        return False


@cache.timed_cache(3)
def squeue() -> results.Result:
    '''
    Get information about jobs managed by slurm using squeue.

    Returns:
        :Result object containing information about the calculation status:

            - **directory (list[str])** – path to slurm directories.
            - **id (list[str])** – slurm job id's.
            - **status (list[str])** – slurm job status name. See squeue documentation.
            - **statuscode (list[str])** – slurm job status codes. See squeue documentation

    .. note::

        By default this function uses a timed cache (see :func:`cache.timed_cache`) with a 3 second delay to lessen the load on HPC systems.
    '''
    ret = results.Result()

    if not has_slurm():
        return ret

    # specify the columns to get here
    columns = ['directory', 'id', 'statuscode', 'status']
    options = ['%Z', '%A', '%t', '%T']  # these are the squeue format codes

    # set each column as an empty list in the return object
    for col in columns:
        ret[col] = []

    # run the squeue command with the formatting options
    output = sp.check_output(['squeue', '--me', '--format', '' + ' '.join(options) + '']).decode()
    output = [line for line in output.splitlines()[1:] if line.strip()]

    # then add the data to the return object's lists
    for line in output:
        [ret[col].append(val) for col, val in zip(columns, line.split())]

    return ret


def sbatch(runfile: str, **options: dict) -> results.Result:
    '''
    Submit a job to slurm using sbatch.

    Args:
        runfile: the path to the filename to be submitted.
        options: options to be used for sbatch.

    Returns:
        A :class:`results.Result` containing the slurm job ID as the ``id`` key and the full command used for submitting the job as the ``command`` key.
    '''
    cmd = 'sbatch '
    for key, val in options.items():
        key = key.replace('_', '-')
        if len(key) > 1:
            cmd += f'--{key}={val} '
        else:
            cmd += f'-{key} {val} '

    cmd = cmd + runfile

    ret = results.Result()
    ret.command = cmd

    # run the job
    sbatch_out = sp.check_output(cmd.split(), stderr=sp.STDOUT).decode()
    # get the slurm job id from the output
    for line in sbatch_out.splitlines():
        if line.startswith('Submitted batch job'):
            # set the slurm job id for this calculation, we use this in order to set dependencies between jobs.
            ret.id = line.strip().split()[-1]
            break

    return ret


def workdir_info(workdir: str) -> results.Result:
    '''
    Function that gets squeue information given a working directory. This will return None if the directory is not being actively referenced by slurm.

    Returns:
        :Result object containing information about the calculation status, see :func:`squeue`.
    '''
    if not has_slurm():
        return None

    sq = squeue()
    if workdir not in sq.directory:
        return None

    workdir_index = sq.directory.index(workdir)
    ret = results.Result()
    for key, vals in sq.items():
        ret[key] = vals[workdir_index]

    return ret


def wait_for_job(slurmid: int, check_every: int = 3):
    '''
    Wait for a slurm job to finish. We check every `check_every` seconds if the slurm job id is still present in squeue.

    Args:
        slurmid: the ID of the slurm job we are waiting for.
        check_every: the amount of seconds to wait before checking squeue again. Don't put this too high, or you will anger the cluster people.
    '''
    while slurmid in squeue().id:
        time.sleep(check_every)


if __name__ == '__main__':
    if has_slurm():
        log.info('This platform has SLURM.')
    else:
        log.info('This platform does not have SLURM.')
