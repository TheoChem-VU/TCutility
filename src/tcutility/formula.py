from typing import Union

from scm import plams


def parse_molecule(molecule: plams.Molecule) -> str:
    """
    Analyse a molecule and return the molstring describing its parts. Each part will then be separated by a + sign in the new string.

    Args:
        molecule: plams.Molecule object to be parsed.

    Returns:
        A string that contains each part of the molecule separated by a + sign, for use in TCutility.formula.molecule function for further formatting.
    """
    # to separate a molecule we need to have bonds
    molecule.guess_bonds()
    parts = []
    # go through each part of the molecule
    for part in molecule.separate():
        # get a dictionary of counts for each element
        form = part.get_formula(True)
        # add all elements with their number, but only if the number is larger than 1.
        # this prevents the creation of strings containing e.g. C1H3Cl2
        parts.append("".join([sym + (str(num) if num > 1 else "") for sym, num in form.items()]))
    return " + ".join(parts)


def molecule(molecule: Union[str, plams.Molecule], mode: str = "unicode") -> str:
    """
    Parse and return a string containing a molecular formula that will show up properly in LaTeX, HTML or unicode.

    Args:
        molecule: plams.Molecule object or a string that contains the molecular formula to be parsed. It can be either single molecule or a reaction. Molecules should be separated by '+' or '->'.
        mode: the formatter to convert the string to. Should be 'unicode', 'html', 'latex', 'pyplot'.

    Returns:
        A string that is formatted to be rendered nicely in either HTML or LaTeX.
    """
    # to take care of plus-signs used to denote reactions we have to first split
    # the molstring into its parts.
    if isinstance(molecule, plams.Molecule):
        molstring = parse_molecule(molecule)
    else:
        molstring = molecule

    for part in molstring.split():
        # if part is only a plus-sign we skip this part. This is only true when the plus-sign
        # is used to denote a reaction
        if part in ["+", "->"]:
            continue

        # parse the part
        partret = part
        # numbers should be subscript
        for num in "0123456789":
            if mode in ["latex", "pyplot"]:
                partret = partret.replace(num, f"_{num}")
            if mode == "html":
                partret = partret.replace(num, f"<sub>{num}</sub>")
            if mode == "unicode":
                partret = partret.replace(num, "₀₁₂₃₄₅₆₇₈₉"[int(num)])

        # signs should be superscript
        for sign in "+-•":
            # negative charges should be denoted by em dash and not a normal dash
            if mode in ["latex", "pyplot"]:
                partret = partret.replace(sign, f'^{sign.replace("-", "—")}')
            if mode == "html":
                partret = partret.replace(sign, f'<sup>{sign.replace("-", "—")}</sup>')
            if mode == "unicode":
                partret = partret.replace(sign, "⁺⁻•"["+-•".index(sign)])
        # replace the part in the original string
        molstring = molstring.replace(part, partret)

    if mode == "pyplot":
        return rf"${molstring}$"

    return molstring


if __name__ == "__main__":
    print(molecule("F- + CH3Cl", "html"))
    mol = plams.Molecule(r"D:\Users\Yuman\Desktop\PhD\TCutility\test\fixtures\chloromethane_sn2_ts\ts sn2.results\output.xyz")
    print(molecule(mol))
