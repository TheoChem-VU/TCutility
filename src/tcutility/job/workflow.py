import multiprocessing as mp
from time import sleep
import numpy as np
from tcutility import log, results, slurm
import inspect
import sys
import jsonpickle
import os
from math import pi
from types import ModuleType
import uuid

import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()


class SkipContext:
    def __enter__(self):
        sys.settrace(lambda *args, **keys: None)
        frame = inspect.currentframe().f_back.f_back
        frame.f_trace = self.trace
        return self

    def trace(self, *args):
        raise


class WorkFlow(SkipContext):
    def __init__(self, name=None, version=None):
        self.name = name
        self.version = version
        self.output = results.Result()
        self.preambles = []
        self.postambles = []
        self.dependency = None

    def add_preamble(self, amble:str):
        self.preambles.append(amble)

    def add_postamble(self, amble:str):
        self.postambles.append(amble)
    
    def add_dependency(self, slurm_id: str):
        if self.dependency is not None: 
            self.dependency += f',{slurm_id}'
        else:
            self.dependency = f'afterok:{slurm_id}'

    def __str__(self):
        return f'WorkFlow(name="{self.name}", version="{self.version}")'

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.set_script(traceback.tb_frame)
        return True

    def set_script(self, frame):
        first_line = frame.f_lineno
        with open(frame.f_code.co_filename) as script:
            lines = script.readlines()[first_line-1:]

        leading_space = lambda line: len(line) - len(line.lstrip())

        code_lines = []

        for line in lines[1:]:
            if line.strip() != '':
                first_not_empty_line = line
                break

        for line in lines[1:]:
            if len(line.strip()) == 0:
                code_lines.append('\n')
            elif leading_space(line) >= leading_space(first_not_empty_line):
                code_lines.append(line[leading_space(first_not_empty_line):])
            else:
                break

        self.script = ''.join(code_lines)
        self.locals = frame.f_locals
        self.globals = frame.f_globals
    

    def execute(self,delete=True,sbatch: dict=None, rundir=None, **inp):
        self.rundir = rundir or f'{self.name}_{self.version}'
        self.input = results.Result(inp)
        if sbatch is None:
            sbatch = {}
        if self.dependency is not None:
            sbatch["dependency"] = self.dependency
        # Use slurm.sbatch here with runscript
        if slurm.has_slurm():
            self.write_script(delete)
            ret = slurm.sbatch(self.batch_name,**sbatch)
            return ret.id
            # slurm.sbatch(self.script_name,**sbatch)
        else:
            exec(self.script, self.globals, self.locals)
            
        return self.output

    def __call__(self,delete=True,sbatch: dict=None, rundir=None, **inp):
        # os.makedirs(os.path.join(rundir, name), exist_ok=True)
        # os.copy()
        # if slurm.has_slurm():
        return self.execute(sbatch=sbatch,delete=delete, rundir=rundir, **inp)

    def write_script(self, delete, **kwargs):
        unique_id = uuid.uuid4()
        file_name = '.' + self.name + '_' + str(unique_id)

        dill_path = f'{file_name}.json'
        d = {'globals': self.globals, 'locals': self.locals}
        with open(dill_path, 'w+') as dill_file:
            dill_file.write(jsonpickle.encode(d))

        with open(f'{file_name}.py', 'w+') as script:
            self.script_name = f'{file_name}.py'
            script.write('#! python\n')
            script.write('import jsonpickle\n')
            script.write('import sys\n\n\n')

            script.write('###### unpickling all necessary variables ######\n')
            script.write(f'with open("{os.path.abspath(dill_path)}", "rb") as dill_file:\n')
            script.write('    objs = jsonpickle.decode(dill_file.read())\n')
            script.write('    locals().update(objs["locals"])\n')
            script.write('    globals().update(objs["globals"])\n\n\n')

            script.write('###### the actual script ######\n')
            script.write(self.script)

        self.batch_name = f'{file_name}.sh'
        with open(self.batch_name, 'w') as file:
            file.write('#!/bin/bash\n\n')

            for line in self.preambles:
                file.write(line+'\n')

            file.write(f'python {self.script_name}\n')

            for line in self.postambles:
                file.write(line+'\n')

            if delete:
                file.write(f'rm {self.script_name}\n')
                file.write(f'rm {dill_path}\n')
                file.write(f'rm {self.batch_name}\n')


# from tcutility import molecule, results
# from tcutility.job import DFTBJob, WorkFlow


# with WorkFlow(name='SN2', version='v1') as wf:
#     # load reactant complex
#     rc = molecule.load(wf.input.rc)

#     # separate the fragments
#     substrate = [atom for atom in rc if atom.flags.frag == 'Substrate']
#     X = [atom for atom in rc if atom.flags.frag == 'X']
#     Y = [atom for atom in rc if atom.flags.frag == 'Y']


#     # optimize the reactants
#     R_EtY = substrate + Y
#     # get the C-Y atoms
#     R_rc = [i + 1 for i, atom in enumerate(R_EtY) if 'anchor_Y' in atom.flags.tags]
#     with DFTBJob(overwrite=False, use_slurm=False) as reactant_opt_substrate:
#         reactant_opt_substrate.sbatch(p='tc', n=8)
#         reactant_opt_substrate.molecule(R_EtY)
#         reactant_opt_substrate.charge(rc.flags.charge_Substrate + rc.flags.charge_Y)
#         reactant_opt_substrate.optimization()
#         reactant_opt_substrate.rundir = wf.rundir
#         reactant_opt_substrate.name = 'R_EtY'

#     with DFTBJob(overwrite=False, use_slurm=False) as reactant_opt_X:
#         reactant_opt_X.sbatch(p='tc', n=8)
#         reactant_opt_X.molecule(X)
#         reactant_opt_X.charge(rc.flags.charge_X)
#         reactant_opt_X.optimization()
#         reactant_opt_X.rundir = wf.rundir
#         reactant_opt_X.name = 'R_X'


#     # optimize the products
#     P_EtX = substrate + X
#     # get the C-X atoms
#     P_rc = [i + 1 for i, atom in enumerate(P_EtX) if 'anchor_X' in atom.flags.tags]
#     with DFTBJob(overwrite=False, use_slurm=False) as product_opt_substrate:
#         product_opt_substrate.sbatch(p='tc', n=8)
#         product_opt_substrate.molecule(P_EtX)
#         product_opt_substrate.charge(rc.flags.charge_Substrate + rc.flags.charge_X)
#         product_opt_substrate.optimization()
#         product_opt_substrate.rundir = wf.rundir
#         product_opt_substrate.name = 'P_EtX'

#     with DFTBJob(overwrite=False, use_slurm=False) as product_opt_Y:
#         product_opt_Y.sbatch(p='tc', n=8)
#         product_opt_Y.molecule(Y)
#         product_opt_Y.charge(rc.flags.charge_Y)
#         product_opt_Y.optimization()
#         product_opt_Y.rundir = wf.rundir
#         product_opt_Y.name = 'P_Y'


#     # do a pesscan
#     R_results = results.read(reactant_opt_substrate.workdir)
#     P_results = results.read(product_opt_substrate.workdir)

#     R_mol = R_results.molecule.output
#     P_mol = P_results.molecule.output

#     R_dist = R_mol[R_rc[0]].distance_to(R_mol[R_rc[1]])
#     P_dist = P_mol[P_rc[0]].distance_to(P_mol[P_rc[1]])

# print(wf)
# wf(rundir='SN2', rc='example.xyz')
