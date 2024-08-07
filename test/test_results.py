from tcutility import results
import os

j = os.path.join


def test_read_dft() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "DFT_EDA"))
    assert isinstance(res, results.Result)


def test_dft_engine() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "DFT_EDA"))
    assert res.engine == "adf"


def test_LOT() -> None:
    # LOT = level of theory
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "DFT_EDA"))
    assert res.level.summary == "OLYP/TZ2P"


def test_LOT2() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "level_of_theory", "MP2_SOS"))
    assert res.level.summary == "MP2-SOS/TZ2P"


def test_LOT3() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "level_of_theory", "PBE0_MBD_rsSC"))
    assert res.level.summary == "PBE0-MBD@rsSC/TZ2P"


def test_LOT4() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "level_of_theory", "M06_2X"))
    assert res.level.summary == "M06-2X/QZ4P"


def test_sections() -> None:
    res = results.read(j(os.path.split(__file__)[0], "fixtures", "DFT_EDA"))
    assert all(section in res for section in ["adf", "engine", "ams_version", "is_multijob", "molecule", "status", "timing"])


def test_failed_reading() -> None:
    res = results.read('not/a/real/calculation')
    assert res.engine == 'unknown'


def test_failed_reading2() -> None:
    res = results.read('not/a/real/calculation')
    assert res.status.code == 'U'


def test_failed_reading3() -> None:
    res = results.read('not/a/real/calculation')
    assert res.status.fatal is True


if __name__ == '__main__':
    import pytest
    pytest.main()
