import attrs
import numpy as np


@attrs.define
class VDDCharge:
    atom_index: int  # index of the atom in the molecules
    atom_symbol: str  # symbol of the atom
    charge: float  # mili-electrons
    frag_index: int  # index of the fragment in the fragments list

    def change_unit(self, ratio: float):
        self.charge *= ratio

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, VDDCharge):
            return False
        return bool(self.atom_index == __value.atom_index and self.atom_symbol == __value.atom_symbol and np.isclose(self.charge, __value.charge, atol=1e-1) and self.frag_index == __value.frag_index)
