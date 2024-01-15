import subprocess as sp
from tcutility import results


def has_slurm():
    try:
        output = sp.check_output(['which', 'sbatch']).decode()
        return True
    except sp.CalledProcessError:
        return False


def squeue():
    ret = results.Result()

    if not has_slurm():
        return ret

    # specify the columns here
    columns = ['directory', 'id', 'status']
    options = ['%Z', '%A', '%t']
    # set each column as an empty list in the return object
    for col in columns:
        ret[col] = []

    # run the squeue command with the formatting options
    output = sp.check_output(['squeue', '--me', '--format', '"' + ' '.join(options) + '"']).decode()
    output = [line for line in output.splitlines()[1:] if line.strip()]

    # then add the data to the return object's lists
    for line in output:
        [ret[col].append(val) for col, val in zip(columns, line.split())]

    return ret


print(has_slurm())
print(squeue())
