from TCutility import results
import os

j = os.path.join


def test_read_dft() -> None:
    res = results.read(j('test', 'fixtures', 'DFT_EDA'))
    assert isinstance(res, results.Result)


def test_dft_engine() -> None:
    res = results.read(j('test', 'fixtures', 'DFT_EDA'))
    assert res.engine == 'adf'


def test_sections() -> None:
    res = results.read(j('test', 'fixtures', 'DFT_EDA'))
    assert all(section in res for section in ['adf', 'engine', 'ams_version', 'history', 'is_multijob', 'molecule', 'status', 'timing'])
