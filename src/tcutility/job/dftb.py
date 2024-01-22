from tcutility.job.ams import AMSJob
import os


j = os.path.join


class DFTBJob(AMSJob):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = None
        self.kspace('Good')
        self.single_point()
        self.model('GFN1-xTB')
        self.solvent('vacuum')

    def kspace(self, quality: str = 'Good'):
        '''
        Set the k-space integration quality for this job.

        Args:
            quality: the type of basis-set to use. Default is TZ2P.
        '''
        self.settings.input.DFTB.kspace.quality = quality

    def model(self, name: str = 'GFN1-xTB', dispersion: str = None, parameter_dir: str = None):
        '''
        Set the model Hamiltonian for the job to use. By default it is set to GFN1-xTB.

        Args:
            name: name of the model Hamiltonian. This is the same name as the one in the DFTB gui.
        '''
        self.settings.input.DFTB.Model = name

        if dispersion is None:
            for disp_suffix in ['-UFF', '-ULG', '-D2', '-D3-BJ', '-D4', '-Auto']:
                if not name.endswith(disp_suffix):
                    continue
                self.settings.input.DFTB.DispersionCorrection = disp_suffix[1:]
                self.settings.input.DFTB.Model[:-len(disp_suffix)]
        else:
            self.settings.input.DFTB.DispersionCorrection = dispersion

        if parameter_dir:
            self.settings.input.DFTB.ResourcesDir = parameter_dir

    def solvent(self, name: str = None, grid_size=974):
        '''
        Model solvation using GBSA.

        Args:
            name: the name of the solvent you want to use. Please see the DFTB manual for a list of available solvents.
            grid_size: the size of the grid used to construct the solvent accessible surface.
        '''
        if name == 'vacuum':
            self.settings.input.DFTB.pop('solvation', None)
            return

        self.settings.input.DFTB.Solvation.Solvent = name
        self.settings.input.DFTB.Solvation.SurfaceGrid = grid_size


if __name__ == '__main__':
    with DFTBJob(test_mode=False, overwrite=True) as job:
        job.rundir = 'tmp/SN2'
        job.name = 'DFTB'
        job.molecule('../../../test/fixtures/xyz/transitionstate_radical_addition.xyz')
        job.sbatch(p='tc', ntasks_per_node=15)
        job.model('GFN1-xTB')
        job.optimization()
        job.kspace('Good')
        job.solvent('H2O')
