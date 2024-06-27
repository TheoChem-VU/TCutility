import pytest
from tcutility.data.basis_set import basis_sets


def test_number_of_orbitals():
    assert basis_sets.number_of_orbitals("Pd", "DZ") == 57


def test_number_of_virtuals():
    assert basis_sets.number_of_virtuals("Pd", "DZ") == 34


if __name__ == "__main__":
    pytest.main()
