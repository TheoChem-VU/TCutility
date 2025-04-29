import inspect
import uuid
import subprocess as sp
import dill
import tcutility
from tcutility import cache, connect
import jsonpickle
import os
import hashlib
import json


def hash(obj):
    '''
    Hash any python object using SHA-256. If the object is a dictionary use JSON to
    put it in a standard format. If there are non-picklable objects
    use jsonpickle to pickle them anyway.
    '''
    if isinstance(obj, dict):
        try:
            obj = json.dumps(obj, sort_keys=True, indent=4)
        except:
            obj = jsonpickle.encode(obj)

    return hashlib.sha256(obj.encode('utf-8')).hexdigest()


@cache.cache
def _python_path(server: connect.Server = connect.Local()):
    """
    Sometimes it is necessary to have the Python path as some environments don't have its path.
    This function attempts to find the Python path and returns it.
    """
    python = ""
    try:
        python = server.execute("which python").strip()
    except sp.CalledProcessError:
        python == ""

    if python == "" or not server.path_exists(python):
        try:
            python = server.execute("which python3").strip()
        except sp.CalledProcessError:
            python == ""

    # we default to the python executable   
    if python == "" or not server.path_exists(python):
        python = "python"

    return python


class workflow:
    def __init__(self, server = None, delete_files: bool = True, preambles: list[str] = None, postambles: list[str] = None, sbatch: dict = None):
        self.preambles = preambles or []
        self.postambles = postambles or []
        self.sbatch = sbatch.copy() or {}
        self.delete_files = delete_files
        self.server = server or tcutility.connect.Local()

    def __call__(self, *args, **kwargs):
        return self._call_method(*args, **kwargs)

    def _call_method(*args, **kwargs):
        self, func = args[:2]
        self.func = func
        self.name = func.__name__
        self.parameters = inspect.signature(func).parameters
        self._call_method = self.execute
        return self

    def __str__(self):
        s = f'WorkFlow({self.name}):\n'
        s += '  Parameters:\n'

        param_names = []
        for param in self.parameters.values():
            p = param.name
            if param.annotation is not param.empty:
                p += f': {param.annotation}'
            param_names.append(p)

        param_name_len = max([len(param) for param in param_names])
        for param in self.parameters.values():
            p = param.name
            if param.annotation is not param.empty:
                p += f': {param.annotation}'

            s += f'    {p.ljust(param_name_len)}'
            if param.kind in [param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY] and param.default is param.empty:
                s += ' REQUIRED'
            s += '\n'
        return s

    def _write_files(self, args: dict):
        unique_id = uuid.uuid4()
        file_name = '.' + self.name + '_' + str(unique_id)

        self.sh_path = f'{file_name}.sh'
        self.py_path = f'{file_name}.py'
        self.out_path = f'{file_name}.out'

        with self.server.open_file(self.py_path, 'w+') as script:
            script.write('#====== LOAD STATE ========#\n')
            script.write('import dill\n')
            script.write('import jsonpickle\n\n')

            for arg_name, arg_val in args.items():
                if arg_name in self.parameters and self.parameters[arg_name].annotation != inspect._empty:
                    annotation = self.parameters[arg_name].annotation
                    if isinstance(annotation, str):
                        annotation = '"' + annotation + '"'
                    else:
                        annotation = annotation.__name__
                    script.write(f'# type: {annotation}\n')
                else:
                    script.write(f'# type: {type(arg_val).__name__}\n')

                try:
                    script.write(f'{arg_name} = dill.loads({dill.dumps(arg_val)})\n\n')
                except dill.PickleError:
                    script.write(f'{arg_name} = jsonpickle.decode(\'{jsonpickle.encode(arg_val, unpicklable=True)}\')\n\n')

            script.write('#========= SCRIPT =========#\n')
            script.write('import tcutility\nimport atexit\n\n\n')
            script.write(f'''@atexit.register
def on_exception():
    if tcutility.job.workflow_db.get_status("{self.hash}") == "RUNNING":
        tcutility.job.workflow_db.set_failed("{self.hash}")\n\n\n''')
            script.write(extract_func_code(self.func))
            script.write(f'\n\n\n# indicate to the db that this wf has finished:\ntcutility.job.workflow_db.set_finished("{self.hash}")\n')

        with self.server.open_file(self.sh_path, 'w') as file:
            file.write('#!/bin/bash\n\n')

            for line in self.preambles:
                file.write(line + '\n')

            file.write(f'{_python_path(self.server)} {self.py_path}\n')

            for line in self.postambles:
                file.write(line + '\n')

            if self.delete_files:
                file.write(f'rm {self.py_path}\n')
                # file.write(f'rm {self.out_path}\n')
                file.write(f'rm {self.sh_path}\n')


    def execute(self, dependency=None, *args, **kwargs):
        self.hash = hash({'wf': self.func, 'args': args, 'kwargs': kwargs})

        if dependency is None:
            dependency = []

        if len(dependency) > 0:
            if any(option not in self.sbatch for option in ['d', 'dependency']):
                self.sbatch.setdefault('dependency', 'afterany')

            for dep in dependency:
                if not hasattr(dep, 'slurm_job_id'):
                    continue
                self.sbatch['dependency'] = self.sbatch['dependency'] + f':{dep.slurm_job_id}'

        if tcutility.job.workflow_db.can_skip(self.hash):
            if tcutility.job.workflow_db.get_status(self.hash) == 'RUNNING':
                tcutility.log.info('Workflow is currently running.')
            elif tcutility.job.workflow_db.get_status(self.hash) == 'SUCCESS':
                tcutility.log.info('Workflow run has already been completed!')
            elif tcutility.job.workflow_db.get_status(self.hash) == 'FAILED':
                tcutility.log.info('Workflow was run but failed')
                
            # Add slurm_job_id to self if it is skippable
            temp_data = tcutility.job.workflow_db.get_data(self.hash)

            if 'slurm_job_id' in temp_data:
                self.slurm_job_id = temp_data["slurm_job_id"]

            box = f'WorkFlow({self.name}):\n    args = (\n'
            for arg in args:
                box += f'        {repr(arg)},\n'
            box += '    )\n    kwargs = {\n'
            for k, v in kwargs.items():
                box += f'        {k}: {repr(v)},\n'
            box += '    }\n'
            box += f'    hash = {self.hash}'

            tcutility.log.boxed(box)
            return

        _args = {}
        for param_name, arg in zip(self.parameters, args):
            _args[param_name] = arg
        _args.update(kwargs)

        for param_name, param in self.parameters.items():
            if param.default != param.empty:
                _args.setdefault(param_name, param.default)

        for glob_name, glob in inspect.getclosurevars(self.func).globals.items():
            _args[glob_name] = glob

        self._write_files(_args)
        if not ruff_check_script(self.py_path, ignored_codes=['E402', 'F811', 'F401']):
            raise Exception('Python script will fail!')

        if tcutility.slurm.has_slurm():
            if any(option not in self.sbatch for option in ["o", "output"]):
                self.sbatch.setdefault("o", self.out_path)
            sbatch_result = tcutility.slurm.sbatch(self.sh_path, self.server, **self.sbatch)
            self.slurm_job_id = sbatch_result.id
            tcutility.job.workflow_db.set_running(self.hash, slurm_job_id=self.slurm_job_id)
        else:
            runfile_dir, runscript = os.path.split(self.sh_path)
            if runfile_dir == '':
                runfile_dir = '.'
            command = ["./" + runscript] if os.name == "posix" else ["sh", runscript]
            self.server.chmod(744, self.sh_path)
            with open(self.out_path, "w+") as out:
                sp.run(command, cwd=runfile_dir, stdout=out, shell=True)
        return self


def extract_func_code(func: callable) -> str:
    '''
    Function used to extract and clean code from a function.
    '''
    # obtain the source code lines from the function
    # this contains still decorators and the function definition
    # which we must remove
    source = inspect.getsource(func)

    # remove lines with decorators, these always start with a @
    source = [line for line in source if not line.strip().startswith('@')]
    flattened = ''.join(source)

    # we first remove annotations given as strings
    # these can contain unclosed parentheses which 
    # would mess up the next step of the cleaning
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if not isinstance(param.annotation, str):
            continue
        # if the annotation is a string we replace it with an empty one
        # in this case we only want to replace the first occurence
        flattened = flattened.replace(param.annotation, '', 1)

    # to remove the function definition we go through the source code
    # by character and count the number of open parentheses
    # the function definition must always have a total of zero parentheses
    # and must also end with a colon
    n_open_para = 0
    for i, char in enumerate(flattened):
        if char == '(':
            n_open_para += 1
        if char == ')':
            n_open_para -= 1
        if n_open_para == 0 and char == ':':
            break
    else:
        print('Could not read function code:')
        print('=============================')
        print(flattened)
        raise ValueError()

    # we then obtain the code_lines
    code_lines = flattened[i+1:].splitlines()

    # the first line is always empty
    # because of our method
    code_lines = code_lines[1:]

    # and also the base_indentation of the function
    for line in code_lines:
        if line.strip() == '':
            continue
        base_indent = len(line) - len(line.lstrip())
        break

    # use base_indentation to properly align code to be all the way left
    code_lines = [line[base_indent:] for line in code_lines]

    return '\n'.join(code_lines)


def ruff_check_script(path: str, ignored_codes=None) -> bool:
    '''
    Check if a python script in `path` will run according to Ruff.

    Args:
        path: a path to the python script to check.
        ignored_codes: the Ruff warning and error codes to ignore.

    Returns:
        A boolean specifying if the return code is 0 or not.
    '''
    if ignored_codes is None:
        ignored_codes = []

    out = sp.run(f'ruff check {path} --ignore {",".join(ignored_codes)}', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # if the ruff check failed we get a non-zero exit
    if out.returncode != 0:
        # simply print the output if we failed
        tcutility.log.log('Found issue when parsing code with Ruff:')
        tcutility.log.boxed(out.stdout.decode())
        # and the code itself
        tcutility.log.log(f'Code ({path}):')
        with open(path) as file:
            tcutility.log.boxed(file.read())
        return False
    return True


if __name__ == '__main__':
    @workflow(
        sbatch={'p': 'rome', 'n': 32, 't': '120:00:00'},
        delete_files=False,
        )
    def sn2(molecule) -> None:
        import tcutility
        print('Test')
        
        with tcutility.job.DFTBJob(use_slurm=False) as job:
            job.molecule(molecule)


    sn2(molecule='abc.xyz')
