from TCutility import formula


def test_single_molecule():
    assert formula.molecule("F-", "html") == "F<sup>—</sup>"


def test_single_molecule2():
    assert formula.molecule("CH3Cl", "html") == "CH<sub>3</sub>Cl"


def test_single_molecule3():
    assert formula.molecule("C6H12O6", "html") == "C<sub>6</sub>H<sub>1</sub><sub>2</sub>O<sub>6</sub>"


def test_reaction():
    assert formula.molecule("F- + CH3Cl", "html") == "F<sup>—</sup> + CH<sub>3</sub>Cl"


def test_reaction2():
    assert formula.molecule("F- + CH3Cl -> CH3F + Cl-", "html") == "F<sup>—</sup> + CH<sub>3</sub>Cl -> CH<sub>3</sub>F + Cl<sup>—</sup>"


if __name__ == "__main__":
    import pytest

    pytest.main()
