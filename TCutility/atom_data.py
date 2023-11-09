import pathlib as pl


# read data
# data_dir = j(os.path.split(__file__)[0], 'atom_data')
data_dir = pl.Path(__file__).parents[0] / 'atom_data'

with open(data_dir / 'name.txt') as data:
    lines = data.readlines()
_element_order = [line.split(',')[1].strip() for line in lines]

with open(data_dir / 'symbol.txt') as data:
    lines = data.readlines()
_symbol_order = [line.split(',')[1].strip() for line in lines]

with open(data_dir / 'radius.txt') as data:
    lines = data.readlines()
_radii = {int(line.split(',')[0]): float(line.split(',')[1].strip()) for line in lines}

with open(data_dir / 'color.txt') as data:
    lines = data.readlines()
_colors = {int(line.split(',')[0]): [int(x.strip()) for x in line.split(',')[1:]] for line in lines}


def parse_element(val):
    if isinstance(val, int):
        return val
    if val.lower() in _element_order:
        return _element_order.index(val.lower()) + 1
    if val in _symbol_order:
        return _symbol_order.index(val) + 1


def radius(element):
    num = parse_element(element)
    return _radii.get(num)


def color(element):
    num = parse_element(element)
    return _colors[num]


if __name__ == '__main__':
    print(color('carbon'))
