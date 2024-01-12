from tcutility import atom_data
import pytest


def test_parse():
    assert atom_data.parse_element("hydrogen") == 1


def test_parse2():
    assert atom_data.parse_element("C") == 6


def test_parse3():
    assert atom_data.parse_element(14) == 14


def test_parse4():
    assert atom_data.parse_element(1) == 1


def test_parse5():
    assert atom_data.parse_element("Carbon") == 6


def test_radius():
    assert atom_data.radius("Tungsten") == 1.62


def test_radius2():
    with pytest.raises(KeyError):
        atom_data.radius("FakeElement")


if __name__ == "__main__":
    pytest.main()
