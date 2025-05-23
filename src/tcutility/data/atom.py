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
        return _element_order.index(val.lower())
    if val in _symbol_order:
        # alternatively try to get it in the symbol list
        return _symbol_order.index(val)
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


def color(element, mode: str = 'rgb'):
    '''
    Args:
        element: the symbol, name or atom number of the element. See :func:`parse_element`.
        mode: the type of color to return. Can be `rgb` or `hex`.

    Return:
        The standard CPK colors of the elements, up to element 109. 
        If the mode is `rgb` returns a tuple of RGB values between `0` and `255`.
    '''
    num = parse_element(element)
    c = _colors[num]
    if mode == 'rgb':
        return c
    if mode == 'hex':
        return '#%02x%02x%02x' % tuple(c)


def atom_number(element):
    return parse_element(element)


def symbol(element):
    num = parse_element(element)
    return _symbol_order[num]


def element(element):
    num = parse_element(element)
    return _element_order[num]


if __name__ == "__main__":
    print(symbol(0))
