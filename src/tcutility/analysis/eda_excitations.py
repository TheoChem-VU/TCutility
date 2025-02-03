from tcutility import results
import numpy as np
import os

try:
    import pyfmo
    has_pyfmo = True
except ModuleNotFoundError:
    has_pyfmo = False


# class EDATransition:
#     def __init__(self,
#                  ):


class EDAExcitation:
    def __init__(self, 
                 exc_idx=-1, 
                 wavelength=0, 
                 photon_energy=0, 
                 osc_strength=0,
                 from_MO_names=None,
                 to_MO_names=None,
                 from_MO_spins=None,
                 to_MO_spins=None,
                 from_orbs=None,
                 to_orbs=None,
                 fragments=None,
                 orbs_complex=None,
                 orbs_frags=None):
        self.exc_idx = exc_idx
        self.wavelength = wavelength
        self.photon_energy = photon_energy * 27.2107  # Ha to eV
        self.osc_strength = osc_strength
        self.from_MO_names = from_MO_names
        self.to_MO_names = to_MO_names
        self.from_MO_spins = from_MO_spins
        self.to_MO_spins = to_MO_spins
        self.from_orbs = from_orbs
        self.to_orbs = to_orbs
        self.fragments = fragments
        self.orbs_frags = orbs_frags
        self.orbs_complex = orbs_complex
        if has_pyfmo:
            self._load_fragment_characters()
        self.transitions = []

    def _load_fragment_characters(self) -> dict:
        '''
        Determine the fragment characters of the from-MO and the to-MO for each transition.

        Returns:
            Dictionary with one key for each fragment. 
            Each value is a list of tuples for each transition in the excitation.
            Each tuple contains the fragment character of the from-MO and the to-MO.
        '''
        self.fragment_characters = {}
        for frag in self.fragments:
            frag_SFOs = [sfo for sfo in self.orbs_complex.sfos if sfo.fragment == frag]
            frag_SFO_idxs = [sfo.index - 1 for sfo in frag_SFOs]
            self.fragment_characters[frag] = []
            for forbs, torbs in zip(self.from_orbs, self.to_orbs):
                forb_character = 1
                for forb in forbs:
                    forb_all_coeffs = self.orbs_complex.data.matrices.coefficients.total[forb.index]
                    forb_frag_coeffs = forb_all_coeffs[frag_SFO_idxs]
                    forb_character *= sum(forb_frag_coeffs**2) / sum(forb_all_coeffs**2)
                    torb_character = 1
                    for torb in torbs:
                        torb_all_coeffs = self.orbs_complex.data.matrices.coefficients.total[torb.index]
                        torb_frag_coeffs = torb_all_coeffs[frag_SFO_idxs]
                        torb_character *= sum(torb_frag_coeffs**2) / sum(torb_all_coeffs**2)

                self.fragment_characters[frag].append((forb_character, torb_character))

    def __str__(self):
        s = f'''Excitation({self.exc_idx}):
    λ   = {self.wavelength: .2f} nm
    h𝛎  = {self.photon_energy: .3f} eV
    f12 = {self.osc_strength: .4f} km/mol
    Transitions:
'''
        for ts in self.transitions:
            s += f'\t\t{ts}\n'
        return s


class EDAExcitations:
    def __init__(self, calc_dir: str):
        self.res_complex = results.read(os.path.join(calc_dir, 'complex'))
        if has_pyfmo:
            self.orbs_complex = pyfmo.orbitals2.objects.Orbitals(self.res_complex.files['adf.rkf'])
            frags = self.orbs_complex.fragments
            self.res_frags = {frag: results.read(os.path.join(calc_dir, f'frag_{frag}')) for frag in frags}
            self.orbs_frags = {frag: pyfmo.orbitals2.objects.Orbitals(self.res_frags[frag].files['adf.rkf']) for frag in frags}
        self._load()

    def _load(self):
        self.excitations = []
        # go through the excitations based on their irreps and types
        for exc_irrep, exc_irrep_data in self.res_complex.properties.excitations.items():
            for exc_type, exc_data in exc_irrep_data.items():
                for exc_idx in range(exc_data.number_of_excitations):
                    energy = exc_data.energies[exc_idx]
                    wavelength = exc_data.wavelengths[exc_idx]
                    osc_strength = exc_data.oscillator_strengths[exc_idx]

                    contributions = exc_data.contributions[exc_idx]
                    from_MO_names = exc_data.from_MO[exc_idx]
                    to_MO_names = exc_data.to_MO[exc_idx]
                    from_MO_spins = exc_data.from_MO_spin[exc_idx]
                    to_MO_spins = exc_data.to_MO_spin[exc_idx]

                    if has_pyfmo:
                        from_orbs = [[mo for mo in self.orbs_complex.mos if mo.name.startswith(MO)] for MO in from_MO_names]
                        to_orbs = [[mo for mo in self.orbs_complex.mos if mo.name.startswith(MO)] for MO in to_MO_names]
                    else:
                        from_orbs = None
                        to_orbs = None

                    exc = EDAExcitation(exc_idx=exc_idx + 1, 
                                        wavelength=wavelength, 
                                        photon_energy=energy, 
                                        osc_strength=osc_strength,
                                        from_MO_names=from_MO_names,
                                        to_MO_names=to_MO_names,
                                        from_MO_spins=from_MO_spins,
                                        to_MO_spins=to_MO_spins,
                                        from_orbs=from_orbs,
                                        to_orbs=to_orbs,
                                        fragments=self.orbs_complex.fragments,
                                        orbs_complex=self.orbs_complex,
                                        orbs_frags=self.orbs_frags,
                                        )
                    self.excitations.append(exc)



if __name__ == '__main__':
    exc = EDAExcitations('/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/tmp/EDA')
    print(exc.excitations[0].fragment_characters)
