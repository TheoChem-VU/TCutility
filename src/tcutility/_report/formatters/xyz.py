from tcutility._report.formatters import generic
from tcutility import results


class Default(generic.DefaultFormatter):
    def _get_data(self, obj: results.Result | str):
        ret = results.Result()
        if isinstance(obj, str):
            obj = results.read(obj)

        ret.E = obj.properties.energy.bond

        # add Gibbs and enthalpy if we have them
        if obj.properties.energy.enthalpy:
            ret.H = obj.properties.energy.enthalpy

        if obj.properties.energy.gibbs:
            ret.G = obj.properties.energy.gibbs

        # add imaginary frequency if we have one
        if obj.properties.vibrations:
            ret.num_imag_modes = obj.properties.vibrations.number_of_imag_modes
            ret.imag_freqs = [f for f in obj.properties.vibrations.frequencies if f < 0]

        ret.molecule = obj.molecule.output

        return ret


    def _format(self, data: results.Result) -> str:
        s = ""
        if data.E:
            s += f"<b><i>E</i></b> = {data.E: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
        if data.H:
            s += f"<b><i>H</i></b> = {data.H: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
        if data.G:
            s += f"<b><i>G</i></b> = {data.G: .2f} kcal mol<sup>-1</sup><br>".replace("-", "–")
        if data.num_imag_modes:
            s += f"N<sub>imag</sub> = {data.num_imag_modes}"
            if data.num_imag_modes > 0:
                freqs = ", ".join([f"{-freq:.1f}<i>i</i>" for freq in data.imag_freqs])
                s += f"({freqs})"
            s += "<br>"

        s = s.removesuffix('<br>')
        s += "<pre>"
        for atom in data.molecule:
            s += f"{atom.symbol:2}    {atom.x: .8f}    {atom.y: .8f}    {atom.z: .8f}<br>"
        s += "</pre>"

        return s





def _hydrogen_bond_format(obj: results.Result, write_str: str) -> str:
    # add electronic energy. E should be bold and italics. Unit will be kcal mol^-1
    E = str(round(obj.properties.energy.bond, 2)).replace("-", "–")
    write_str += f"<b><i>E</i></b> = {E} kcal mol<sup>—1</sup><br>"

    # add Gibbs and enthalpy if we have them
    if obj.properties.energy.enthalpy:
        H = str(round(obj.properties.energy.enthalpy, 2)).replace("-", "–")
        write_str += f"<b><i>H</i></b> = {H} kcal mol<sup>—1</sup><br>"
    if obj.properties.energy.gibbs:
        G = str(round(obj.properties.energy.gibbs, 2)).replace("-", "–")
        write_str += f"<b><i>G</i></b> = {G} kcal mol<sup>—1</sup><br>"

    # add imaginary frequency if we have one
    if obj.properties.vibrations:
        num_imag_modes = obj.properties.vibrations.number_of_imag_modes

        # We only want to write nimag = 0 if there are no imaginary modes
        if num_imag_modes < 1:
            return write_str + "<b><i>ν<sub>imag</sub></i></b> = 0"

        # Otherwise we write the imaginary frequencies
        freqs = [
            abs(round(f))
            for f in obj.properties.vibrations.frequencies[:num_imag_modes]
        ]

        freqs_str = ", ".join(f"{f}<i>i</i>" for f in freqs)
        write_str += f"<b><i>ν<sub>imag</sub></i></b> = {num_imag_modes} ({freqs_str}) cm<sup>–1</sup>"

    return write_str
