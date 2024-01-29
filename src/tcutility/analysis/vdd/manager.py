from __future__ import annotations

import copy
import functools
import pathlib as pl
from itertools import zip_longest
from typing import Dict, List, Optional, Sequence, Union

import attrs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import tcutility.log as log
from tcutility.analysis.vdd import charge
from tcutility.constants import VDD_UNITS
from tcutility.results import result

PRINT_FORMAT = {"me": "%+.0f", "e": "%+.3f"}


def change_unit_decorator(func):
    @functools.wraps(func)
    def wrapper(self, unit: str = "me", *args, **kwargs):
        current_unit = self.unit
        self.change_unit(unit)
        result = func(self, *args, **kwargs)
        self.change_unit(current_unit)
        return result

    return wrapper


def create_vdd_charge_manager(results: result.Result) -> VDDChargeManager:
    """Create a VDDChargeManager from a Result object."""
    vdd_charges: Dict[str, List[charge.VDDCharge]] = {}
    atom_symbols = results.molecule.atom_symbols  # type: ignore
    frag_indices = results.molecule.frag_indices  # type: ignore
    calc_dir = pl.Path(results.files["root"])  # type: ignore
    is_fragment_calculation = results.adf.used_regions  # type: ignore
    mol_charge = results.molecule.mol_charge  # type: ignore

    # Convert the VDD charges to VDDCharge objects
    for irrep, charge_array in results.properties.vdd.items():  # type: ignore
        irrep = "vdd" if irrep == "charges" else irrep
        vdd_charges[irrep] = []
        for atom_index, (frag_index, vdd_charge) in enumerate(zip(frag_indices, charge_array)):
            atom_symbol = atom_symbols[atom_index]
            vdd_charges[irrep].append(charge.VDDCharge(atom_index + 1, atom_symbol, vdd_charge, frag_index))

    return VDDChargeManager(vdd_charges, is_fragment_calculation, calc_dir, mol_charge)


@attrs.define
class VDDChargeManager:
    """Class to manage the VDD charges. It can be used to print the VDD charges in a nice table and write them to a text file or excel file."""

    vdd_charges: Dict[str, List[charge.VDDCharge]]  # {"vdd": [VDDCharge, ...], "irrep1": [VDDCharge, ...], ...}
    is_fragment_calculation: bool
    calc_dir: pl.Path
    mol_charge: int
    name: str = attrs.field(init=False)
    unit: str = attrs.field(init=False, default="e")  # unit of the VDD charges. Available units are "me" (mili-electrons) and "e" (electrons)
    irreps: List[str] = attrs.field(init=False, default=set())

    def __attrs_post_init__(self):
        self.irreps = list(self.vdd_charges.keys())
        self.name = self.calc_dir.name if self.calc_dir is not None else self.name
        self.change_unit("me")
        log.info(f"VDDChargeManager created for {self.name}")

    def __str__(self) -> str:
        """Prints the VDD charges in a nice table. Checks if the calculation is a fragment calculation and prints the summed VDD charges if it is."""
        individual_charges_table = self.get_vdd_charges_table()
        summed_charges_table = self.get_summed_vdd_charges_table()

        ret_str = f"{self.name}\nVDD charges (in unit {self.unit}):\n{individual_charges_table}\n\n"
        if self.is_fragment_calculation:
            ret_str += f"Summed VDD charges (in unit {self.unit}):\n{summed_charges_table}\n"

        return ret_str

    def charge_is_conserved(self) -> bool:
        """Check if the total charge of the molecule is conserved. The total charge is the sum of the VDD charges."""
        tolerance = 1e-4 if self.unit == "e" else 1e-1
        is_conserved = np.isclose(self.mol_charge, sum([charge.charge for charge in self.vdd_charges["vdd"]]), atol=tolerance)
        return is_conserved  # type: ignore since numpy _bool is not recognized as bool

    def change_unit(self, new_unit: str) -> None:
        """Change the unit of the VDD charges. Available units are "me" (mili-electrons) and "e" (electrons)."""
        if new_unit not in VDD_UNITS:
            raise ValueError(f"Unit {new_unit} is not available. Choose from {VDD_UNITS.keys()}")

        if new_unit == self.unit:
            return

        ratio = VDD_UNITS[new_unit] / VDD_UNITS[self.unit]
        [charge.change_unit(ratio) for charges in self.vdd_charges.values() for charge in charges]
        self.unit = new_unit

    @change_unit_decorator
    def get_vdd_charges(self) -> Dict[str, List[charge.VDDCharge]]:
        """Get the VDD charges in the specified unit ([me] or [e])."""
        return copy.deepcopy(self.vdd_charges)

    @change_unit_decorator
    def get_summed_vdd_charges(self, irreps: Optional[Sequence[str]] = None) -> Dict[str, Dict[str, float]]:
        """Get the summed VDD charges per fragment for the specified unit ([me] or [e])."""
        irreps = irreps if irreps is not None else self.irreps
        summed_vdd_charges: Dict[str, Dict[str, float]] = {}

        for irrep in irreps:
            summed_vdd_charges[irrep] = {}
            for vdd_charge in self.vdd_charges[irrep]:
                frag_index = str(vdd_charge.frag_index)
                summed_vdd_charges[irrep].setdefault(frag_index, 0.0)
                summed_vdd_charges[irrep][frag_index] += vdd_charge.charge

        return copy.deepcopy(summed_vdd_charges)

    def get_vdd_charges_dataframe(self) -> pd.DataFrame:
        """Get the VDD charges as a pandas DataFrame in a specified unit ([me] or [e])."""
        frag_indices = [charge.frag_index for charge in self.vdd_charges["vdd"]]
        atom_symbols = [f"{charge.atom_index}{charge.atom_symbol}" for charge in self.vdd_charges["vdd"]]
        charges = [[charge.charge for charge in charges] for _, charges in self.vdd_charges.items()]
        headers = ["Frag", "Atom"] + [irrep for irrep, _ in self.vdd_charges.items()]
        combined_table = list(zip_longest(frag_indices, atom_symbols, *charges, fillvalue=""))
        df = pd.DataFrame(combined_table, columns=headers).rename(columns={"vdd": "Total"})
        return df

    def get_summed_vdd_charges_dataframe(self) -> pd.DataFrame:
        """Get the summed VDD charges as a pandas DataFrame in a specified unit ([me] or [e])."""
        summed_data = self.get_summed_vdd_charges()
        summed_data["Frag"] = {str(key): int(key) for key in summed_data["vdd"].keys()}
        df = pd.DataFrame(summed_data).pipe(lambda df: df[df.columns.tolist()[-1:] + df.columns.tolist()[:-1]])  # move the "Frag" column to the front
        return df.rename(columns={"vdd": "Total"})

    def get_vdd_charges_table(self) -> str:
        df = self.get_vdd_charges_dataframe()
        return df.to_string(float_format=lambda x: PRINT_FORMAT[self.unit] % x, justify="center", index=False, col_space=6)

    def get_summed_vdd_charges_table(self) -> str:
        df = self.get_summed_vdd_charges_dataframe()
        return df.to_string(float_format=lambda x: PRINT_FORMAT[self.unit] % x, justify="center", col_space=6, index=False)

    @staticmethod
    def write_to_txt(output_dir: Union[str, pl.Path], managers: Union[VDDChargeManager, Sequence[VDDChargeManager]], unit: str = "me") -> None:
        """Write the VDD charges to a text file. It is a static method because multiple managers can be written to the same file."""
        out_dir = pl.Path(output_dir) if not isinstance(output_dir, pl.Path) else output_dir
        files = [out_dir / "VDD_charges_per_atom.txt", out_dir / "VDD_charges_per_fragment.txt"]
        managers = managers if isinstance(managers, Sequence) else [managers]

        # Print charges per atom and per fragment in seperate files
        for i, file in enumerate(files):
            with open(file, "w") as f:
                f.write("VDD charges:\n")
                for manager in managers:
                    f.write(f"{manager.name} (unit = {manager.unit})\n")
                    if i == 0:
                        f.write(manager.get_vdd_charges_table())
                    else:
                        f.write(manager.get_summed_vdd_charges_table()) if manager.is_fragment_calculation else f.write("No fragment calculation\n")
                    f.write("\n\n")

    def write_to_excel(self, output_file: Optional[Union[str, pl.Path]] = None) -> None:
        """Write the VDD charges to an excel file. Results are written to two sheets: "VDD charges" and "Summed VDD charges"."""
        file = pl.Path(output_file) if output_file is not None else self.calc_dir / f"vdd_charges_{self.name}.xlsx"
        file = file.with_suffix(".xlsx") if not file.suffix == ".xlsx" else file

        df = self.get_vdd_charges_dataframe()

        with pd.ExcelWriter(file) as writer:
            df.to_excel(writer, sheet_name=f"VDD charges (in {self.unit})", index=False, float_format=PRINT_FORMAT[self.unit])
            if self.is_fragment_calculation:
                df_summed = self.get_summed_vdd_charges_dataframe()
                df_summed.to_excel(writer, sheet_name=f"Summed VDD charges  (in {self.unit})", index=False, float_format=PRINT_FORMAT[self.unit])

    def plot_vdd_charges_per_atom(self, output_file: Optional[Union[str, pl.Path]] = None, unit: str = "me") -> None:
        """Plot the VDD charges as a bar graph for each irrep."""
        file = pl.Path(output_file) if output_file is not None else self.calc_dir / f"vdd_charges_{self.name}.png"
        file = file.with_suffix(".png") if not file.suffix == ".png" else file
        self.change_unit(unit)

        # Increase the global font size
        plt.rcParams.update({"font.size": 14})

        num_irreps = len(self.vdd_charges)
        n_max_charges = max([len(charges) for charges in self.vdd_charges.values()])
        _, axs = plt.subplots(num_irreps, 1, figsize=(n_max_charges * 1.15, 5 * num_irreps), sharey=True)
        axs = [axs] if num_irreps == 1 else axs

        # Initialize a variable to keep track of the most positive/negative values
        adjusted_abs_max_values = []

        counter = 1
        for ax, (irrep, charges) in zip(axs, self.vdd_charges.items()):
            atom_symbols = [f"{charge.atom_index}{charge.atom_symbol} ({charge.frag_index})" for charge in charges]
            charge_values = [charge.charge for charge in charges]

            bars = ax.bar(atom_symbols, charge_values, color="sandybrown", edgecolor="black")
            if counter == len(axs):
                ax.set_xlabel("Atom (#Fragment Number)")
            ax.set_ylabel(f"Charge ({unit})")
            ax.set_title(f"VDD Charges {self.name} - {irrep}")
            ax.yaxis.grid(True)  # Only display vertical grid lines

            # Add the charge value on top of each bar. If the value is negative, place the text below the bar
            for bar in bars:
                yval = bar.get_height()
                x_pos = bar.get_x() + bar.get_width() / 2

                if yval <= 0:
                    ax.text(x_pos, yval + yval * 0.1, int(yval), va="top", ha="center")
                else:
                    ax.text(x_pos, yval + yval * 0.1, int(yval), va="bottom", ha="center")
                adjusted_abs_max_values.append(yval + yval * 0.1)
            counter += 1

        # Making sure the values do not extend outside the plot. Also determines the y-axis limits for all subplotss
        min_value, max_value = min(adjusted_abs_max_values), max(adjusted_abs_max_values)

        # Axes adjustments
        # Set the y-axis limits for all subplots based on the most positive/negative values
        for ax in axs:
            ax.set_ylim([min_value - abs(min_value) * 0.2, max_value + abs(max_value) * 0.2])

        # plt.tight_layout()
        plt.savefig(file, dpi=300)
