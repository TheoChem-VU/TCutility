import attrs


@attrs.define
class VDDCharge:
    atom_index: int  # index of the atom in the molecules
    atom_symbol: str  # symbol of the atom
    charge: float  # mili-electrons
    frag_index: int  # index of the fragment in the fragments list

    def change_unit(self, ratio: float):
        self.charge *= ratio
