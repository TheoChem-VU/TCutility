import tcutility
import os
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from scm import plams


def read(path):
    return PyFragResult(path)


class PyFragResult:
    def __init__(self, path, step_prefix: str = 'Step.'):
        self.path = path

        self._frag_results = {}
        self._step_results = []
        self._order = []
        self._mask = []
        self._properties = {}

        self.step_prefix = step_prefix

        self._load()

    def _load(self):
        for frag_path, info in tcutility.pathfunc.match(self.path, 'frag_{frag}').items():
            self._frag_results[info.frag] = tcutility.results.read(frag_path)
        for step_path, info in tcutility.pathfunc.match(self.path, self.step_prefix + '{step}', sort_by='step').items():
            self._step_results.append({})
            for dir_name in os.listdir(step_path):
                p = os.path.join(step_path, dir_name)
                res = tcutility.results.read(p)
                self._step_results[-1][dir_name] = res

            self._order.append(int(info.step.removeprefix('0')))
            self._mask.append(True)

        self._mask = np.array(self._mask)

    def get_property(self, key: str, calc: str = 'complex'):
        if key in self._properties:
            return self._properties[key][self._order][self._mask[self._order]]
        p = np.array([res[calc].properties.get_multi_key(key) for res in self._step_results])
        return p[self._order][self._mask[self._order]]

    @property
    def fragments(self):
        return list(self._frag_results.keys())

    def __len__(self):
        return sum(self._mask)

    def get_geometry(self, *args, **kwargs):
        calc = kwargs.pop('calc', 'complex')
        g = np.array([tcutility.geometry.parameter(res[calc].molecule.input, *args, **kwargs) for res in self._step_results])
        return g[self._order][self._mask[self._order]]

    def get_molecules(self, calc: str = 'complex') -> List[plams.Molecule]:
        mols = [res[calc].molecule.input for res in self._step_results]
        return mols
        return [mols[int(i)] for i in np.array(self._order)[self._mask[self._order]]]

    def sort_by(self, val: str or list, calc: str = 'complex'):
        if isinstance(val, str):
            val = self.get_property(val, calc=calc)
        self._order = np.argsort(val)

    def set_mask(self, mask: list):
        self._mask = mask

    def set_coord(self, coord: list):
        self._coord = coord

    def coord(self):
        return self._coord[self._order][self._mask[self._order]]

    def set_property(self, name: str, vals):
        self._properties[name] = vals

    @property
    def ts_idx(self):
        energies = self.total_energy()
        for i in range(len(self) - 2, 1, -1):
            if energies[i-1] < energies[i] and energies[i] < energies[i+1]:
                return i + 1

    def total_energy(self):
        return self.interaction_energy() + self.strain_energy()

    def interaction_energy(self):
        return self.get_property('energy.bond', 'complex')

    def strain_energy(self, fragment: str = None):
        if fragment is None:
            t = 0
            for frag in self.fragments:
                t += self.strain_energy(frag)
            return t

        return self.get_property('energy.bond', f'frag_{fragment}') - self._frag_results[fragment].properties.energy.bond

    def overlap(self, orb1, orb2, calc: str = 'complex', absolute: bool = True):
        S = np.array([orb.sfos[orb1] @ orb.sfos[orb2] for orb in self.orbs(calc)])
        if absolute:
            S = abs(S)
        return S[self._order][self._mask[self._order]]

    def orbital_energy_gap(self, orb1, orb2, calc: str = 'complex'):
        dE = np.array([abs(orb.sfos[orb1].energy - orb.sfos[orb2].energy) for orb in self.orbs(calc)])
        return dE[self._order][self._mask[self._order]]
    def sfo_coefficient(self, sfo, mo, calc: str = 'complex'):
        C = np.array([orb.sfos[sfo].coefficient(orb.mos[mo]) for orb in self.orbs(calc)])
        return C[self._order][self._mask[self._order]]

    @tcutility.cache.cache
    def orbs(self, calc: str = 'complex'):
        try:
            import pyfmo
        except ModuleNotFoundError:
            raise ModuleNotFoundError('The pyfmo module could not be loaded. To gain access please contact the TCutility developers!')

        return [pyfmo.Orbitals(res[calc].files['adf.rkf']) for res in self._step_results]


if __name__ == '__main__':
    res_C = read('/Users/yumanhordijk/PhD/Projects/RadicalAdditionASMEDA/data/DFT/TS_C_O/PyFrag_OLYP_TZ2P')
    res_X = read('/Users/yumanhordijk/PhD/Projects/RadicalAdditionASMEDA/data/DFT/TS_X_O/PyFrag_OLYP_TZ2P')
    
    res_C.set_coord(res_C.get_geometry(0, 1))
    res_X.set_coord(res_X.get_geometry(1, 2))

    res_C.sort_by(res_C.coord())
    res_X.sort_by(res_X.coord())

    plt.figure()
    plt.plot(res_C.coord(), res_C.overlap('Methyl(SOMO)_A', 'Substrate(LUMO)_A'), label='C-addition')
    plt.plot(res_X.coord(), res_X.overlap('Methyl(SOMO)_A', 'Substrate(LUMO)_A'), label='X-addition')
    plt.ylabel(r'$\langle SOMO | LUMO \rangle$')
    plt.legend()
    plt.xlim(3, 2.2)

    plt.figure()
    plt.plot(res_C.coord(), res_C.orbital_energy_gap('Methyl(SOMO)_A', 'Substrate(LUMO)_A'), label='C-addition')
    plt.plot(res_X.coord(), res_X.orbital_energy_gap('Methyl(SOMO)_A', 'Substrate(LUMO)_A'), label='X-addition')
    plt.ylabel(r'$|\epsilon_{SOMO} - \epsilon_{LUMO}|$')
    plt.legend()
    plt.xlim(3, 2.2)

    plt.figure()
    plt.plot(res_C.coord(), res_C.overlap('Methyl(LUMO)_B', 'Substrate(7A_B)_B'), label='C-addition')
    plt.plot(res_X.coord(), res_X.overlap('Methyl(LUMO)_B', 'Substrate(7A_B)_B'), label='X-addition')
    plt.ylabel(r'$\langle SUMO | HOMO \rangle$')
    plt.legend()
    plt.xlim(3, 2.2)

    plt.figure()
    plt.plot(res_C.coord(), res_C.orbital_energy_gap('Methyl(LUMO)_B', 'Substrate(7A_B)_B'), label='C-addition')
    plt.plot(res_X.coord(), res_X.orbital_energy_gap('Methyl(LUMO)_B', 'Substrate(7A_B)_B'), label='X-addition')
    plt.ylabel(r'$|\epsilon_{SUMO} - \epsilon_{HOMO}|$')
    plt.legend()
    plt.xlim(3, 2.2)

    plt.show()
