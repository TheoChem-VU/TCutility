import pathlib as pl


# read data
data_dir = pl.Path(__file__).parents[0] / "_atom_data_info"

with open(data_dir / "name.txt") as data:
    lines = data.readlines()
_element_order = [line.split(",")[1].strip() for line in lines]

with open(data_dir / "symbol.txt") as data:
    lines = data.readlines()
_symbol_order = [line.split(",")[1].strip() for line in lines]

with open(data_dir / "radius.txt") as data:
    lines = data.readlines()
_radii = {int(line.split(",")[0]): float(line.split(",")[1].strip()) for line in lines}

with open(data_dir / "color.txt") as data:
    lines = data.readlines()
_colors = {int(line.split(",")[0]): [int(x.strip()) for x in line.split(",")[1:]] for line in lines}


def parse_element(val):
    """
    Parse a str or int to an atom number.

    Args:
        val: Element name, symbol or atom number.

    Returns:
        Atom number corresponding to val.

    Examples:

        .. code-block:: python

            parse_element('Hydrogen') == 1
            parse_element('C') == 6
            parse_element(23) == 23
    """
    # we will assume an integer value is an atom number already
    if isinstance(val, int):
        return val
    # if it is not an int it should be a string
    if val.lower() in _element_order:
        # first try to get it in the element name list
        return _element_order.index(val.lower()) + 1
    if val in _symbol_order:
        # alternatively try to get it in the symbol list
        return _symbol_order.index(val) + 1
    raise KeyError(f'Element "{val}" not parsable.')


def radius(element):
    '''
    Args:
        element: the symbol, name or atom number of the element. See :func:`parse_element`.
    Return: 
        The empirical covalent radius of an element in angstroms, up to element 96.
    '''
    num = parse_element(element)
    return _radii.get(num)


def color(element):
    '''
    Args:
        element: the symbol, name or atom number of the element. See :func:`parse_element`.

    Return:
        The standard CPK colors of the elements, up to element 109.
    '''
    num = parse_element(element)
    return _colors[num]


if __name__ == "__main__":
    print(color("carbon"))
