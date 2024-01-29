import subprocess as sp
from tcutility import results, log


def has_slurm() -> bool:
    '''
    Function to check if the current platform uses slurm. 

    Returns:
        has_slurm: whether slurm is available on this platform.
    '''
    try:
        sp.check_output(['which', 'sbatch']).decode()
        return True
    except sp.CalledProcessError:
        return False


def squeue() -> results.Result:
    '''
    Get information about jobs managed by slurm using squeue.

    Returns:
        :Result object containing information about the calculation status:

            - **directory (list[str])** – path to slurm directories.
            - **id (list[str])** – slurm job id's.
            - **status (list[str])** – slurm job status name. See squeue documentation.
            - **statuscode (list[str])** – slurm job status codes. See squeue documentation
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


if __name__ == '__main__':
    if has_slurm():
        log.info('This platform has SLURM.')
    else:
        log.info('This platform does not have SLURM.')