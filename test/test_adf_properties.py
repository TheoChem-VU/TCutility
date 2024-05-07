import pathlib as pl

import pytest
from tcutility import results


@pytest.fixture()
def ethane_res() -> results.Result:
    return results.read(pl.Path(__file__).parent / "fixtures" / "ethane_adf")


@pytest.fixture()
def unrestricted_res() -> results.Result:
    return results.read(pl.Path(__file__).parent / "fixtures" / "radical_addition_ts/geometry")


def test_energy_terms(ethane_res):
    print(ethane_res.keys())
    assert ethane_res.properties.energy.gibbs == pytest.approx(-522.38, abs=1e-2)
    assert ethane_res.properties.energy.enthalpy == pytest.approx(-507.64, abs=1e-2)
    assert ethane_res.properties.energy.nuclear_internal == pytest.approx(29.09, abs=1e-2)


def test_s2_restricted(ethane_res):
    assert ethane_res.properties.s2 == 0
    assert ethane_res.properties.s2_expected == 0
    assert ethane_res.properties.spin_contamination == 0


def test_s2_spinpol1(unrestricted_res):
    assert round(unrestricted_res.properties.s2, 5) == 0.75845
    assert unrestricted_res.properties.s2_expected == 0.75
    assert round(unrestricted_res.properties.spin_contamination, 4) == 0.0113


if __name__ == '__main__':
    pytest.main()
