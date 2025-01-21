import tcutility
import os
import numpy as np
import matplotlib.pyplot as plt

def read(path):
    return PyFragResult(path)


class PyFragResult:
    def __init__(self, path):
        self.path = path

        self._frag_results = {}
        self._step_results = []
        self._order = []
        self._mask = []

        self._load()

    def _load(self):
        for frag_path, info in tcutility.pathfunc.match(self.path, 'frag_{frag}').items():
            self._frag_results[info.frag] = tcutility.results.read(frag_path)

        for step_path, info in tcutility.pathfunc.match(self.path, 'Step.{step}', sort_by='step').items():
            self._step_results.append({})
            for dir_name in os.listdir(step_path):
                p = os.path.join(step_path, dir_name)
                res = tcutility.results.read(p)
                self._step_results[-1][dir_name] = res

            self._order.append(int(info.step.removeprefix('0')))
            self._mask.append(True)

        self._mask = np.array(self._mask)

    def get_property(self, key: str, calc: str = 'complex'):
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

    def sort_by(self, val: str or list, calc: str = 'complex'):
        if isinstance(val, str):
            val = self.get_property(val, calc=calc)
        self._order = np.argsort(val)

    def set_mask(self, mask: list):
        self._mask = mask

    @property
    def ts_idx(self):
        energies = self.get_property('energy.bond', 'complex')
        for i in range(1, len(self) - 1):
            if energies[i-1] < energies[i] and energies[i] < energies[i+1]:
                return i

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

    def overlap(self, orb1, orb2, calc: str = 'complex'):
        S = np.array([orb.sfos[orb1] @ orb.sfos[orb2] for orb in self.orbs(calc)])
        return S[self._order][self._mask[self._order]]

    def sfo_coefficient(self, sfo, mo, calc: str = 'complex'):
        C = np.array([orb.sfos[sfo].coefficient(orb.mos[mo]) for orb in self.orbs(calc)])
        return C[self._order][self._mask[self._order]]

    @tcutility.cache.cache
    def orbs(self, calc: str = 'complex'):
        try:
            import pyfmo.orbitals2.objects
        except ImportError:
            raise ImportError('pyfmo is not installed. Please install it using `pip install pyfmo`')

        return [pyfmo.orbitals2.objects.Orbitals(res[calc].files['adf.rkf']) for res in self._step_results]

if __name__ == '__main__':
    res = read('/Users/yumanhordijk/PhD/Projects/RadicalAdditionASMEDA/data/DFT/TS_C_O/PyFrag_OLYP_TZ2P')
    res.sort_by(res.get_geometry(0, 1))
    res.set_mask(res.get_geometry(0, 1) < res.get_geometry(0, 1)[res.ts_idx])
    # plt.plot(res.get_geometry(0, 1), res.total_energy())
    # plt.plot(res.get_geometry(0, 1), res.interaction_energy())
    # plt.plot(res.get_geometry(0, 1), res.strain_energy())
    # plt.xlim(3, 2.2)
    # plt.show()

    plt.plot(res.get_geometry(0, 1), abs(res.overlap('Substrate(7A_A)', 'Methyl(5A_A)')))
    plt.plot(res.get_geometry(0, 1), abs(res.overlap('Substrate(4A_A)', 'Methyl(5A_A)')))
    plt.plot(res.get_geometry(0, 1), abs(res.overlap('Substrate(3A_A)', 'Methyl(5A_A)')))
    # Px_coeff = res.sfo_coefficient('C(1P:x)', '7A_A', calc='frag_Substrate')
    # Py_coeff = res.sfo_coefficient('C(1P:y)', '7A_A', calc='frag_Substrate')
    # Pz_coeff = res.sfo_coefficient('C(1P:z)', '7A_A', calc='frag_Substrate')
    # plt.plot(res.get_geometry(0, 1), np.sqrt(Px_coeff**2 + Py_coeff**2 + Pz_coeff**2))
    plt.xlim(3, 2.2)
    plt.show()
