#!/usr/bin/env python3

import os
from tcutility.job import DFTBJob, ADFJob
from tcutility import log, molecule

j = os.path.join


def main(inp, output_dir=None, keep_calcs=False, level=None):
    inp_files = []
    if os.path.isfile(inp):
        inp_files.append(inp)
    elif os.path.isdir(inp):
        for file in os.listdir(inp):
            inp_files.append(j(inp, file))
    else:
        raise ValueError(f"Path {inp} could not be found!")

    input_dir = os.path.split(inp_files[0])[0]
    if output_dir is None:
        output_dir = input_dir + "_optimized"
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    level = level or "GFN1-xTB"

    log.flow(f"Starting pre-optimization for {len(inp_files)} molecules.", ["start"])
    log.flow(f"Level of theory:  {level}")
    log.flow(f"Root directory:   {input_dir}")
    log.flow(f"Output directory: {output_dir}")
    log.flow()

    for i, file in enumerate(inp_files):
        mol = molecule.load(file)
        mol_name = os.path.split(file)[1].removesuffix(".xyz")

        if level in ["GFN1-xTB", "DFTB"]:
            with DFTBJob(test_mode=False, overwrite=True) as job:
                job.molecule(file)
                job.optimization()
                job.vibrations(False)
                job.rundir = ".tmp"
                job.name = mol_name
                job.charge(mol.flags.charge or 0)

                job.add_postamble(f"cp {job.output_mol_path} {j(output_dir, mol_name + '.xyz')}")
                if not keep_calcs:
                    job.add_postamble(f"rm -r {job.workdir}")

        else:
            level_parts = level.split("/")
            if len(level_parts) == 1:
                functional = level_parts[0]
                basis_set = "TZ2P"

            if len(level_parts) == 2:
                functional, basis_set = level_parts

            with ADFJob(test_mode=False, overwrite=True) as job:
                job.molecule(file)
                job.optimization()
                job.vibrations(False)
                job.rundir = ".tmp"
                job.name = mol_name
                job.charge(mol.flags.charge or 0)
                job.spin_polarization(mol.flags.spinpol or 0)
                job.functional(functional)
                job.basis_set(basis_set)

                job.sbatch(p="tc", n=32)
                job.add_postamble(f"cp {job.output_mol_path} {j(output_dir, mol_name + '.xyz')}")
                if not keep_calcs:
                    job.add_postamble(f"rm -r {job.workdir}")

        log.flow(f"{i + 1}/{len(inp_files)}: {os.path.split(file)[1]}: {job.slurm_job_id}", ["split"])

    log.flow()
    log.flow("Finished, goodbye", ["startinv"])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="tcutility.job preoptimize")
    parser.add_argument("input", help="the input xyz-file or directory of xyz-files to optimize.")
    parser.add_argument("-o", "--output_dir", help="the output directory to store the optimized structures.", type=str)
    parser.add_argument("-k", "--keep-calcs", help="whether to keep the calculation directories of the optimization.", action="store_true")
    parser.add_argument("-l", "--level", help='the level of theory to optimize at. By default it is set to "GFN1-xTB".', type=str)

    args = parser.parse_args()
    main(args.input, output_dir=args.output_dir, keep_calcs=args.keep_calcs, level=args.level)
