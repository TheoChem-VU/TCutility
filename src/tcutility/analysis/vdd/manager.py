from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Sequence, Union
import attrs
import pathlib as pl
from itertools import zip_longest
from tcutility.analysis.vdd import charge
from tcutility.results import result


AVAILABLE_UNITS_RATIO = {"me": 1000, "e": 1}
PRINT_FORMAT = {"me": "%+.0f", "e": "%+.3f"}


def create_vdd_charge_manager(results: result.Result, name: str = "VDDChargeManager") -> VDDChargeManager:
    """Create a VDDChargeManager from a Result object."""
    vdd_charges: Dict[str, List[charge.VDDCharge]] = {}
    atom_symbols = results.molecule.atom_symbols  # type: ignore
    frag_indices = results.molecule.frag_indices  # type: ignore

    # Convert the VDD charges to VDDCharge objects
    for irrep, charge_array in results.properties.vdd.items():  # type: ignore
        irrep = "vdd" if irrep == "charges" else irrep
        vdd_charges[irrep] = []
        for atom_index, (frag_index, vdd_charge) in enumerate(zip(frag_indices, charge_array)):
            atom_symbol = atom_symbols[atom_index]
            vdd_charges[irrep].append(charge.VDDCharge(atom_index + 1, atom_symbol, vdd_charge, frag_index))

    return VDDChargeManager(vdd_charges, name)


@attrs.define
class VDDChargeManager:
    """Class to manage the VDD charges. It can be used to print the VDD charges in a nice table and write them to a text file or excel file."""

    vdd_charges: Dict[str, List[charge.VDDCharge]]  # {"vdd": [VDDCharge, ...], "irrep1": [VDDCharge, ...], ...}
    name: str = "VDDChargeManager"  # name of the VDDChargeManager
    unit: str = attrs.field(init=False, default="e")  # unit of the VDD charges. Available units are "me" (mili-electrons) and "e" (electrons)
    irreps: List[str] = attrs.field(init=False, default=set())

    def __attrs_post_init__(self):
        self.irreps = list(self.vdd_charges.keys())
        self.change_unit("me")

    def __str__(self) -> str:
        """Prints the VDD charges in a nice table. Checks if the calculation is a fragment calculation and prints the summed VDD charges if it is."""
        individual_charges_table = self.get_vdd_charges_table(self.unit)
        summed_charges_table = self.get_summed_vdd_charges_table(self.unit)

        ret_str = f"{self.name}\nVDD charges (in unit {self.unit}):\n{individual_charges_table}"
        if self.is_fragment_calculation:
            ret_str += f"\n\nSummed VDD charges (in unit {self.unit}):\n{summed_charges_table}\n"

        return ret_str

    @property
    def is_fragment_calculation(self) -> bool:
        """Check if the calculation is a fragment calculation by checking if the highest fragment index is equal to the number of atoms."""
        return max([charge.frag_index for charges in self.vdd_charges.values() for charge in charges]) == len(self.vdd_charges["vdd"])

    def charge_is_conserved(self, mol_charge: int) -> bool:
        """Check if the total charge of the molecule is conserved. The total charge is the sum of the VDD charges."""
        current_unit = self.unit
        self.change_unit("e")
        is_conserved = np.isclose(mol_charge, sum([charge.charge for charge in self.vdd_charges["vdd"]]), atol=1e-4)
        self.change_unit(current_unit)
        return is_conserved  # type: ignore since numpy _bool is not recognized as bool

    def change_unit(self, new_unit: str) -> None:
        """Change the unit of the VDD charges. Available units are "me" (mili-electrons) and "e" (electrons)."""
        if new_unit not in AVAILABLE_UNITS_RATIO:
            raise ValueError(f"Unit {new_unit} is not available. Choose from {AVAILABLE_UNITS_RATIO.keys()}")

        if new_unit == self.unit:
            return

        ratio = AVAILABLE_UNITS_RATIO[new_unit] / AVAILABLE_UNITS_RATIO[self.unit]
        [charge.change_unit(ratio) for charges in self.vdd_charges.values() for charge in charges]
        self.unit = new_unit

    def get_vdd_charges(self, unit: str) -> Dict[str, List[charge.VDDCharge]]:
        """Get the VDD charges in the specified unit."""
        self.change_unit(unit)
        return self.vdd_charges

    def get_summed_vdd_charges(self, unit: str = "me", irreps: Optional[Sequence[str]] = None) -> Dict[str, Dict[str, float]]:
        """Get the summed VDD charges per fragment."""
        irreps = irreps if irreps is not None else self.irreps
        self.change_unit(unit)
        summed_vdd_charges: Dict[str, Dict[str, float]] = {}

        for irrep in irreps:
            summed_vdd_charges[irrep] = {}
            for vdd_charge in self.vdd_charges[irrep]:
                frag_index = str(vdd_charge.frag_index)
                summed_vdd_charges[irrep].setdefault(frag_index, 0.0)
                summed_vdd_charges[irrep][frag_index] += vdd_charge.charge

        return summed_vdd_charges

    def get_vdd_charges_dataframe(self, unit: str = "me") -> pd.DataFrame:
        """Get the VDD charges as a pandas DataFrame."""
        self.change_unit(unit)
        frag_indices = [charge.frag_index for charge in self.vdd_charges["vdd"]]
        atom_symbols = [f"{charge.atom_index}{charge.atom_symbol}" for charge in self.vdd_charges["vdd"]]
        charges = [[charge.charge for charge in charges] for _, charges in self.vdd_charges.items()]
        headers = ["Frag", "Atom"] + [irrep for irrep, _ in self.vdd_charges.items()]
        combined_table = list(zip_longest(frag_indices, atom_symbols, *charges, fillvalue=""))
        df = pd.DataFrame(combined_table, columns=headers).rename(columns={"vdd": "Total"})
        return df

    def get_summed_vdd_charges_dataframe(self, unit: str = "me") -> pd.DataFrame:
        """Get the summed VDD charges as a pandas DataFrame."""
        summed_data = self.get_summed_vdd_charges(unit)
        summed_data["Frag"] = {str(key): int(key) for key in summed_data["vdd"].keys()}
        df = pd.DataFrame(summed_data).pipe(lambda df: df[df.columns.tolist()[-1:] + df.columns.tolist()[:-1]])  # move the "Frag" column to the front
        return df.rename(columns={"vdd": "Total"})

    def get_vdd_charges_table(self, unit: str = "me") -> str:
        df = self.get_vdd_charges_dataframe(unit)
        return df.to_string(float_format=lambda x: PRINT_FORMAT[self.unit] % x, justify="center", index=False, col_space=6)

    def get_summed_vdd_charges_table(self, unit: str = "me") -> str:
        df = self.get_summed_vdd_charges_dataframe(unit)
        return df.to_string(float_format=lambda x: PRINT_FORMAT[self.unit] % x, justify="center", col_space=6, index=False)

    @staticmethod
    def write_to_txt(output_dir: Union[str, pl.Path], managers: Union[VDDChargeManager, Sequence[VDDChargeManager]], unit: str = "me") -> None:
        """Write the VDD charges to a text file."""
        out_dir = pl.Path(output_dir) if not isinstance(output_dir, pl.Path) else output_dir
        files = [out_dir / "VDD_charges_per_atom.txt", out_dir / "VDD_charges_per_fragment.txt"]
        managers = managers if isinstance(managers, Sequence) else [managers]

        # Print charges per atom and per fragment in seperate files
        for i, file in enumerate(files):
            with open(file, "w") as f:
                f.write(f"VDD charges (in unit {unit}):\n")
                for manager in managers:
                    f.write(f"{manager.name}\n")
                    if i == 0:
                        f.write(manager.get_vdd_charges_table(unit))
                    else:
                        f.write(manager.get_summed_vdd_charges_table(unit))
                    f.write("\n\n")

    def write_to_excel(self, output_dir: Union[str, pl.Path], unit: str = "me") -> None:
        """Write the VDD charges to an excel file. Results are written to two sheets: "VDD charges" and "Summed VDD charges"."""
        out_dir = pl.Path(output_dir) if not isinstance(output_dir, pl.Path) else output_dir
        file = out_dir / f"vdd_charges_{self.name}.xlsx"
        df = self.get_vdd_charges_dataframe(unit)

        with pd.ExcelWriter(file) as writer:
            df.to_excel(writer, sheet_name=f"VDD charges (in {unit})", index=False, float_format=PRINT_FORMAT[self.unit])
            if self.is_fragment_calculation:
                df_summed = self.get_summed_vdd_charges_dataframe(unit)
                df_summed.to_excel(writer, sheet_name=f"Summed VDD charges  (in {unit})", index=False, float_format=PRINT_FORMAT[self.unit])
