from tcutility import job, results
from scm import plams


def load(xyz):
    mol = plams.Molecule()
    for line in xyz.strip().splitlines():
        el, x, y, z = line.split()[:4]
        mol.add_atom(plams.Atom(symbol=el, coords=(x, y, z)))
    return mol

mol = load("""
N       0.00000000       0.00000000       0.81411087
H       0.47592788      -0.82433127       1.14462651
H       0.47592788       0.82433127       1.14462651
H      -0.95185576       0.00000000       1.14462651
B       0.00000000       0.00000000      -0.83480980
H      -0.58140445      -1.00702205      -1.13772686
H      -0.58140445       1.00702205      -1.13772686
H       1.16280890       0.00000000      -1.13772686
""")

# optimize mol
with job.ADFJob() as opt_job:
    opt_job.rundir = 'Elstat'
    opt_job.name = 'Opt'
    opt_job.molecule(mol)
    opt_job.optimization()
    opt_job.functional('BP86')
    opt_job.basis_set('TZP')
    opt_job.quality('Good')
    opt_job.sbatch(p='tc', N=1, t='240:00:00', ntasks_per_node=8)


with job.ADFFragmentJob(decompose_elstat=True) as frag_job:
    frag_job.molecule(opt_job.output_mol_path)
    frag_job.rundir = 'Elstat'
    frag_job.name = 'EDA'
    frag_job.functional('BP86')
    frag_job.basis_set('TZP')
    frag_job.quality('Good')
    frag_job.settings.input.adf.PRINT += ' EKin'

    frag_job.add_fragment([1, 2, 3, 4], 'Donor')
    frag_job.add_fragment([5, 6, 7, 8], 'Acceptor')
    frag_job.sbatch(p='tc', N=1, t='240:00:00', ntasks_per_node=8)


res_main = results.read('Elstat/EDA/complex_STOFIT')
print(res_main.properties.energy.elstat)


res_acceptor = results.read('Elstat/EDA/complex_Acceptor_NoElectrons')
print(res_acceptor.properties.energy.elstat)


res_donor = results.read('Elstat/EDA/complex_Donor_NoElectrons')
print(res_donor.properties.energy.elstat)


print('Electrostatic Potential Terms:')
print(f'  e–e repulsion:                   {res_main.properties.energy.elstat.Vee: 10.0f} kcal/mol')
print(f'  N–N repulsion:                   {res_main.properties.energy.elstat.Vnn: 10.0f} kcal/mol')
print(f'  e(Donor)–N(Acceptor) attraction: {res_acceptor.properties.energy.elstat.Ven: 10.0f} kcal/mol')
print(f'  N(Donor)–e(Acceptor) attraction: {res_donor.properties.energy.elstat.Ven: 10.0f} kcal/mol')
print(f'  total:                           {res_main.properties.energy.elstat.total: 10.1f} kcal/mol')
