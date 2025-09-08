from tcutility.job import ORCAJob
from tcutility import molecule


test_mode = False
sbatch = dict(p="tc", n=32, mem=224000, t="120:00:00")

mol = molecule.load("RC_C2H4_CH3.xyz")
frags = molecule.guess_fragments(mol)

# for each fragment we do an optimization and single point on the complex geometry
for fragname, fragmol in frags.items():
    with ORCAJob(test_mode=test_mode) as job:
        job.molecule(fragmol)
        job.optimization()
        job.name = f"frag_{fragname}_GO"
        job.spin_polarization(fragmol.flags.get("spinpol", 0))
        job.sbatch(**sbatch)
        job.rundir = "calculations"
        job.add_preamble("export PATH=/scistor/tc/dra480/bin/ompi411/bin:$PATH")
        job.add_preamble("export LD_LIBRARY_PATH=/scistor/tc/dra480/bin/ompi411/lib/:$LD_LIBRARY_PATH")
        job.orca_path = "/scistor/tc/dra480/bin/orca500/orca"
        job.settings.mdci.UseQROs = "True"
        [job.settings.main.add(key) for key in "CCSD(T) CC-pVTZ TightSCF UNO".split()]

    with ORCAJob(test_mode=test_mode) as job:
        job.molecule(fragmol)
        job.name = f"frag_{fragname}_SP"
        job.spin_polarization(fragmol.flags.get("spinpol", 0))
        job.sbatch(**sbatch)
        job.rundir = "calculations"
        job.add_preamble("export PATH=/scistor/tc/dra480/bin/ompi411/bin:$PATH")
        job.add_preamble("export LD_LIBRARY_PATH=/scistor/tc/dra480/bin/ompi411/lib/:$LD_LIBRARY_PATH")
        job.orca_path = "/scistor/tc/dra480/bin/orca500/orca"
        job.settings.mdci.UseQROs = "True"
        [job.settings.main.add(key) for key in "CCSD(T) CC-pVTZ TightSCF UNO".split()]

    with ORCAJob(test_mode=test_mode) as job:
        job.molecule(mol)
        job.name = f"complex_frag_{fragname}_BS"
        job.spin_polarization(sum([fragmol.flags.get("spinpol", 0) for fragmol in frags.values()]) - fragmol.flags.get("spinpol", 0))
        job.ghost_atoms([mol.atoms.index(atom) + 1 for atom in fragmol])
        job.sbatch(**sbatch)
        job.rundir = "calculations"
        job.add_preamble("export PATH=/scistor/tc/dra480/bin/ompi411/bin:$PATH")
        job.add_preamble("export LD_LIBRARY_PATH=/scistor/tc/dra480/bin/ompi411/lib/:$LD_LIBRARY_PATH")
        job.orca_path = "/scistor/tc/dra480/bin/orca500/orca"
        job.settings.mdci.UseQROs = "True"
        [job.settings.main.add(key) for key in "CCSD(T) CC-pVTZ TightSCF UNO".split()]

with ORCAJob(test_mode=test_mode) as job:
    job.molecule(mol)
    job.name = "complex"
    job.spin_polarization(sum([fragmol.flags.get("spinpol", 0) for fragmol in frags.values()]))
    job.sbatch(**sbatch)
    job.rundir = "calculations"
    job.add_preamble("export PATH=/scistor/tc/dra480/bin/ompi411/bin:$PATH")
    job.add_preamble("export LD_LIBRARY_PATH=/scistor/tc/dra480/bin/ompi411/lib/:$LD_LIBRARY_PATH")
    job.orca_path = "/scistor/tc/dra480/bin/orca500/orca"
    job.settings.mdci.UseQROs = "True"
    [job.settings.main.add(key) for key in "CCSD(T) CC-pVTZ TightSCF UNO".split()]
