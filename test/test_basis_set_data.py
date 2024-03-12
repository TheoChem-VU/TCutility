from tcutility.data import basis_sets
import pytest


def test_number_of_orbitals():
    assert basis_sets.number_of_orbitals("Pd", "DZ") == 57


def test_number_of_virtuals():
    assert basis_sets.number_of_virtuals("Pd", "DZ") == 34


if __name__ == "__main__":
    pytest.main()
