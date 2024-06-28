from dataclasses import dataclass
from typing import TypeVar

import scm.plams as plams
from tcutility import results
from tcutility.results import Result


@dataclass
class XYZData:
    E: float | None = None
    H: float | None = None
    G: float | None = None
    num_imag_modes: int | None = None
    imag_freqs: list[float] | None = None
    molecule: plams.Molecule | None = None


T = TypeVar("T")


def try_to_get_property(obj: Result, prop: str, def_type: T) -> T | None:
    try:
        property_ = getattr(obj.properties.energy, prop)  # type: ignore  # Result object has no static typing
        if property_ is not None and property_:
            return property_
    except AttributeError:
        return None


def check_if_job_is_suitable_for_xyz_format(obj: Result | str) -> bool:
    """
    Only jobs that are geometry optimizations, single points, or transition state searches are suitable for XYZ format.
    Other calculations such as PES scans, IRCs, etc. are not suitable.
    """
    if isinstance(obj, str):
        obj = results.read(obj)

    if obj is None or not obj:
        return False

    try:
        task = obj.input.task  # type: ignore  # Result object has no static typing
    except AttributeError:
        task = "unknown"

    if not task:
        return False

    return task.lower() in ["geometryoptimization", "singlepoint", "transitionstatesearch"]  # type: ignore  # Result object has no static typing


def get_data_for_xyz_format(obj: results.Result) -> XYZData:
    return_data = XYZData(E=None, H=None, G=None, num_imag_modes=None, imag_freqs=None, molecule=None)
    if not obj.properties or obj.properties is None:
        return return_data

    return_data.E = try_to_get_property(obj, "bond", 0.0)  # Total electronic energy
    return_data.H = try_to_get_property(obj, "enthalpy", 0.0)  # Enthalpy
    return_data.G = try_to_get_property(obj, "gibbs", 0.0)  # Gibbs free energy

    # add imaginary frequency if we have one
    if obj.properties.vibrations:  # type: ignore  # Result object has no static typing
        if obj.properties.vibrations is not None:
            return_data.num_imag_modes = obj.properties.vibrations.number_of_imag_modes  # type: ignore  # Result object has no static typing
            return_data.imag_freqs = [f for f in obj.properties.vibrations.frequencies if f < 0]  # type: ignore  # Result object has no static typing

    return_data.molecule = obj.molecule.output  # type: ignore  # Result object has no static typing
    return return_data


def format_xyz(data: XYZData) -> str:
    s = ""
    if data.E is not None:
        s += f"<b><i>E</i></b> = {data.E: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
    if data.H is not None:
        s += f"<b><i>H</i></b> = {data.H: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
    if data.G is not None:
        s += f"<b><i>G</i></b> = {data.G: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
    if data.num_imag_modes is not None:
        s += f"N<sub>imag</sub> = {data.num_imag_modes} "
        if data.num_imag_modes > 0 and data.imag_freqs is not None:
            freqs = ", ".join([f"{-freq:.1f}<i>i</i>" for freq in data.imag_freqs])
            cm_1 = "cm<sup>-1</sup>".replace("-", "–")
            s += f"({freqs} {cm_1})<br>"
        s += "<br>"

    s = s.removesuffix("<br>")

    if data.molecule is not None:
        s += "<pre>"
        for atom in data.molecule:
            s += f"{atom.symbol:2}    {atom.x: .8f}    {atom.y: .8f}    {atom.z: .8f}<br>"
        s += "</pre>"
    return s


class XYZFormatter:
    def format(self, results: results.Result) -> str:
        write_str = ""

        # The program will crash whwen trying to get data from a calculation, so check before proceeding
        if not check_if_job_is_suitable_for_xyz_format(results):
            return write_str

        data = get_data_for_xyz_format(results)
        write_str += format_xyz(data)
        return write_str
