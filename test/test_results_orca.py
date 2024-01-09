from TCutility import results, constants
import os

j = os.path.join


def test_read_orca() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert isinstance(res, results.Result)


def test_read_orca2() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "sp_freq"))
    assert isinstance(res, results.Result)


def test_read_engine() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert res.engine == "orca"


def test_read_engine2() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "sp_freq"))
    assert res.engine == "orca"


def test_LOT() -> None:
    # LOT = level of theory
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert res.level.summary == "QRO-CCSD(T)/cc-pVTZ"


def test_character() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "sp_freq"))
    assert res.properties.vibrations.character == "transitionstate"


def test_imag_freq() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "sp_freq"))
    assert res.properties.vibrations.frequencies[0] == -47.03


def test_hf_energy() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.energy.HF, 2) == round(-132.433551362 * constants.HA2KCALMOL, 2)


def test_mp2_energy() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.energy.MP2, 2) == round(-132.935938324 * constants.HA2KCALMOL, 2)


def test_ccsd_energy() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.energy.CCSD, 2) == round(-132.964383423 * constants.HA2KCALMOL, 2)


def test_ccsd_t_energy() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.energy.CCSD_T, 2) == round(-132.986982793 * constants.HA2KCALMOL, 2)


def test_t1() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.t1, 5) == round(0.013815962, 5)


def test_s2() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.s2, 5) == round(0.759369, 5)


def test_spin_contam() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "orca", "optimization"))
    assert round(res.properties.spin_contamination * 100, 2) == 1.25


if __name__ == "__main__":
    import pytest

    pytest.main()
