import os
from typing import Tuple

from tcutility.job.adf import ADFJob
from tcutility.job.generic import Job

j = os.path.join


class NMRJob(Job):
    """
    A job that handles calculation of Nuclear Magnetic Resonance (NMR) chemical shifts.
    The job will first run an :class:`tcutility.job.adf.ADFJob` calculation at the SAOP/TZ2P level of theory to prepare for the NMR program of AMS.
    The NMR shifts will be calculated for all atoms and any additional coordinate (NICS).
    New NICS points can be given using the :meth:`NMRJob.add_nics_point` method.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pre_nmr_job = ADFJob(*args, **kwargs)
        self.pre_nmr_job.functional("SAOP")
        self.pre_nmr_job.basis_set("TZ2P")
        self.pre_nmr_job.settings.input.adf.save = "TAPE10"
        self.nics_points = []

    def _setup_job(self):
        os.makedirs(self.workdir, exist_ok=True)

        # set up the pre_nmr_job
        self.pre_nmr_job.rundir = self.rundir
        self.pre_nmr_job.name = self.name + "_pre"
        self.pre_nmr_job.molecule(self._molecule or self._molecule_path)
        self.pre_nmr_job.sbatch(**self._sbatch)

        # we have to add the NICS points in the pre_nmr_job
        multipole_coords = []
        for point in self.nics_points:
            multipole_coords.append(f"        {point[0]} {point[1]} {point[2]} 0.0")
        self.pre_nmr_job.settings.input.ams.System.ElectrostaticEmbedding.MultipolePotential.Coordinates = "\n" + "\n".join(multipole_coords) + "\n      End"

        # we copy the pre_nmr_job output files to the main job directory
        self.pre_nmr_job.add_postamble(f'cp {j(self.pre_nmr_job.workdir, "adf.rkf")} {j(self.workdir, "TAPE21")}')
        self.pre_nmr_job.add_postamble(f'cp {j(self.pre_nmr_job.workdir, "TAPE10")} {j(self.workdir, "TAPE10")}')
        self.pre_nmr_job.run()

        # some extra settings for the main job
        self.dependency(self.pre_nmr_job)
        # NMR will name the calculation as TAPE21 instead of adf.rkf, so we rename it here
        self.add_postamble(f'mv {j(self.workdir, "TAPE21")} {j(self.workdir, "adf.rkf")}')

        # write the input for the NMR job
        # the ghost block holds the NICS points
        ghost_block = "\t"
        if len(self.nics_points) > 0:
            ghost_block += "Ghosts\n"
            for point in self.nics_points:
                ghost_block += f"    {point[0]} {point[1]} {point[2]}\n"
            ghost_block += "SubEnd\n"

        # write input and runfile
        with open(self.inputfile_path, "w+") as inpf:
            inpf.write("NMR\n")
            inpf.write("\tout all\n")
            inpf.write(ghost_block + "\n")
            inpf.write("End\n")

        with open(self.runfile_path, "w+") as runf:
            runf.write("#!/bin/sh\n\n")  # the shebang is not written by default by ADF
            runf.write("\n".join(self._preambles) + "\n\n")
            runf.write(f"$AMSBIN/nmr {self.inputfile_path} < /dev/null\n")
            runf.write("\n".join(self._postambles))

        return True

    def add_nics_point(self, coordinate: Tuple[float, float, float]):
        """
        Add a NICS point to be calculated.

        Args:
            coordinate: the (x, y, z) coordinates of a NICS point to calculate the chemical shift for. Has to be given as cartesian coordinates and using unit angstrom.
        """
        self.nics_points.append(coordinate)


if __name__ == "__main__":
    with NMRJob(test_mode=True) as job:
        job.molecule(r"D:\Users\Yuman\Desktop\PhD\TCutility\examples\job\water_dimer.xyz")
        job.add_nics_point([0, 1, 2])
        job.add_nics_point([0, 1, 2])
        job.add_nics_point([0, 1, 2])
        job.add_nics_point([0, 1, 2])
        job.add_nics_point([0, 1, 2])
        job.add_nics_point([0, 1, 2])
