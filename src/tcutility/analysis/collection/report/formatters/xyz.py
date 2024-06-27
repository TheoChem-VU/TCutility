from dataclasses import dataclass

import scm.plams as plams
from tcutility import results


@dataclass
class XYZData:
    E: float | None = None
    H: float | None = None
    G: float | None = None
    num_imag_modes: int | None = None
    imag_freqs: list[float] | None = None
    molecule: plams.Molecule | None = None


def check_if_job_is_suitable_for_xyz_format(obj: results.Result | str) -> bool:
    """
    Only jobs that are geometry optimizations, single points, or transition state searches are suitable for XYZ format.
    Other calculations such as PES scans, IRCs, etc. are not suitable.
    """
    if isinstance(obj, str):
        obj = results.read(obj)

    return obj.input.task.lower() in ["geometryoptimization", "singlepoint", "transitionstatesearch"]  # type: ignore  # Result object has no static typing


def get_data_for_xyz_format(obj: results.Result | str) -> XYZData:
    E: float = obj.properties.energy.bond  # type: ignore  # Result object has no static typing

    # add Gibbs and enthalpy if we have them
    if obj.properties.energy.enthalpy:  # type: ignore  # Result object has no static typing
        H: float = obj.properties.energy.enthalpy  # type: ignore  # Result object has no static typing

    if obj.properties.energy.gibbs:  # type: ignore  # Result object has no static typing
        G: float = obj.properties.energy.gibbs  # type: ignore  # Result object has no static typing

    # add imaginary frequency if we have one
    if obj.properties.vibrations:  # type: ignore  # Result object has no static typing
        num_imag_modes: int = obj.properties.vibrations.number_of_imag_modes  # type: ignore  # Result object has no static typing
        imag_freqs: list[float] = [f for f in obj.properties.vibrations.frequencies if f < 0]  # type: ignore  # Result object has no static typing

    molecule: plams.Molecule = obj.molecule.output  # type: ignore  # Result object has no static typing

    return XYZData(E, H, G, num_imag_modes, imag_freqs, molecule)


def format_xyz(data: XYZData) -> str:
    s = ""
    if data.E:
        s += f"<b><i>E</i></b> = {data.E: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
    if data.H:
        s += f"<b><i>H</i></b> = {data.H: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
    if data.G:
        s += f"<b><i>G</i></b> = {data.G: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
    if data.num_imag_modes:
        s += f"N<sub>imag</sub> = {data.num_imag_modes}"
        if data.num_imag_modes > 0 and data.imag_freqs is not None:
            freqs = ", ".join([f"{-freq:.1f}<i>i</i>" for freq in data.imag_freqs])
            s += f"({freqs})"
        s += "<br>"

    s = s.removesuffix("<br>")

    if data.molecule is not None:
        s += "<pre>"
        for atom in data.molecule:
            s += f"{atom.symbol:2}    {atom.x: .8f}    {atom.y: .8f}    {atom.z: .8f}<br>"
        s += "</pre>"

    return s


class XYZFormatter:
    def write(self, *results: results.Result | str) -> str:
        write_str = ""
        for obj in results:
            data = get_data_for_xyz_format(obj)
            write_str += format(data)
        return write_str
