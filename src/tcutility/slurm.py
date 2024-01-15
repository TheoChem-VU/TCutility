import subprocess as sp
from tcutility import results, log


def has_slurm():
    try:
        sp.check_output(['which', 'sbatch']).decode()
        return True
    except sp.CalledProcessError:
        return False


def squeue():
    ret = results.Result()

    if not has_slurm():
        return ret

    # specify the columns here
    columns = ['directory', 'id', 'statuscode', 'status']
    options = ['%Z', '%A', '%t', '%T']
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


if __name__ == '__main__':
    if has_slurm():
        log.info('This platform has SLURM.')
    else:
        log.info('This platform does not have SLURM.')