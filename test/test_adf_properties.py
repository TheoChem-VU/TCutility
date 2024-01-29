import pathlib as pl

import pytest
from tcutility import results


@pytest.fixture()
def ethane_res() -> results.Result:
    return results.read(pl.Path(__file__).parent / "fixtures" / "ethane_adf")


def test_energy_terms(ethane_res):
    print(ethane_res.keys())
    assert ethane_res.properties.energy.gibbs == pytest.approx(-522.38, abs=1e-2)
    assert ethane_res.properties.energy.enthalpy == pytest.approx(-507.64, abs=1e-2)
    assert ethane_res.properties.energy.nuclear_internal == pytest.approx(29.09, abs=1e-2)
