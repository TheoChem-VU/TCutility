import inspect
import uuid
import subprocess
import dill
import tcutility


class workflow:
    def __init__(self, server = None, delete_files: bool = True, preambles: list[str] = None, postambles: list[str] = None, sbatch: dict = None):
        self.preambles = preambles or []
        self.postambles = postambles or []
        self.sbatch = sbatch or {}
        self.delete_files = delete_files
        self.server = server or tcutility.connect.Local()

    def __call__(self, *args, **kwargs):
        return self._call_method(*args)

    def _call_method(*args, **kwargs):
        self, func = args[:2]
        self.func = func
        self.name = func.__name__
        self.parameters = inspect.signature(func).parameters
        self._call_method = self.execute
        return self

    def __str__(self):
        s = f'WorkFlow({self.name}):\n'
        s += f'  Parameters:\n'

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
        self.pkl_path = f'{file_name}.pkl'

        with self.server.open_file(self.pkl_path, 'wb+') as pkl:
            dill.dump_module(pkl)

        with self.server.open_file(self.py_path, 'w+') as script:
            script.write('#====== LOAD STATE ========#\n')
            script.write('import dill\n')
            script.write(f'dill.load_module("{file_name}.pkl")\n\n')

            for arg_name, arg_val in args.items():
                annotation = self.parameters[arg_name].annotation
                if isinstance(annotation, str):
                    annotation = '"' + annotation + '"'
                else:
                    annotation = annotation.__name__
                script.write(f'# type: {annotation}\n')
                script.write(f'{arg_name} = dill.loads({dill.dumps(arg_val)})\n\n')

            script.write('#========= SCRIPT =========#\n')
            script.write(extract_func_code(self.func))

        with self.server.open_file(self.sh_path, 'w') as file:
            file.write('#!/bin/bash\n\n')

            for line in self.preambles:
                file.write(line + '\n')

            file.write(f'python {self.py_path}\n')

            for line in self.postambles:
                file.write(line + '\n')

            if self.delete_files:
                file.write(f'rm {self.py_path}\n')
                file.write(f'rm {self.pkl_path}\n')
                file.write(f'rm {self.sh_path}\n')

    def execute(self, *args, **kwargs):
        _args = {}
        for param_name, arg in zip(self.parameters, args):
            _args[param_name] = arg
        _args.update(kwargs)
        print(inspect.getclosurevars(self.func))
        self._write_files(_args)
        # tcutility.connect.


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


def test():
    ...


@workflow()
def sn2(molecule: 'path' = (1, 2, 3), 
        sbatch: dict = None) -> None:
    test()

    with tcutility.job.DFTBJob(test_mode=True) as job:
        job.molecule(molecule)


# print(inspect.getclosurevars(sn2.func))
# print(workflow)
# print(sn2)
sn2({'molecule': 'abc.xyz', 'sbatch': {'p': 'tc', 'n': 32}})
