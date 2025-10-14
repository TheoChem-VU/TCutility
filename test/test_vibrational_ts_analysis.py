from pathlib import Path

import numpy as np
import pytest

from tcutility.analysis.vibration import ts_vibration
from tcutility.results.read import read
from tcutility.results.result import Result


@pytest.fixture
def sn2_path() -> Path:
    return Path(__file__).parent / "fixtures" / "chloromethane_sn2_ts"


@pytest.fixture
def sn2_result() -> Result:
    return read(Path(__file__).parent / "fixtures" / "chloromethane_sn2_ts")


@pytest.fixture
def rad_path() -> Path:
    return Path(__file__).parent / "fixtures" / "radical_addition_ts"


@pytest.fixture
def rad_result() -> Result:
    return read(Path(__file__).parent / "fixtures" / "radical_addition_ts")


def test_sn2_determine_rc(sn2_result) -> None:
    assert np.array_equal(ts_vibration.determine_ts_reactioncoordinate(sn2_result), np.array([[1, 2, 1], [1, 6, -1]]))


def test_rad_determine_rc_1(rad_result) -> None:
    assert np.array_equal(ts_vibration.determine_ts_reactioncoordinate(rad_result, min_delta_dist=0.1), np.array([[1, 16, -1]]))


def test_rad_determine_rc_2(rad_result) -> None:
    assert np.array_equal(ts_vibration.determine_ts_reactioncoordinate(rad_result, min_delta_dist=0.0), np.array([[1, 2, 1], [1, 8, 1], [1, 16, -1], [8, 9, -1]]))


def test_validate_sn2_ts_1(sn2_path) -> None:
    result = ts_vibration.validate_transitionstate(sn2_path, [[1, 2, 1], [1, 6, -1]])
    assert result is True


def test_validate_sn2_ts_2(sn2_path) -> None:
    result = ts_vibration.validate_transitionstate(sn2_path, [[2, 3, 1], [1, 6, -1]])
    assert result is False  # [2,3,1] should not be present


def test_validate_rad_ts_1(rad_path) -> None:
    result = ts_vibration.validate_transitionstate(rad_path)
    assert result is True


def test_validate_rad_ts_2(rad_path) -> None:
    result = ts_vibration.validate_transitionstate(rad_path, [1, 16, 1], min_delta_dist=0.1)
    assert result is True


def test_validate_rad_ts_3(rad_path) -> None:
    result = ts_vibration.validate_transitionstate(rad_path, [[9, 8, -3], [16, 1, -5]], min_delta_dist=0.0)
    assert result is True  # Testing user input normalization


def test_validate_rad_ts_4(rad_path) -> None:
    result = ts_vibration.validate_transitionstate(rad_path, [1, 16])
    assert result is True


def test_validate_rad_ts_5(rad_path) -> None:
    result = ts_vibration.validate_transitionstate(rad_path, [8, 9, 1], min_delta_dist=0.1)
    assert result is False  # Should not be present with this min_delta_dist parameter value


def test_validate_rad_ts_6(rad_path) -> None:
    result = ts_vibration.validate_transitionstate(rad_path, [[1, 16, 1], [8, 9, -1]])
    assert result is False  # Should have equal signs


def test_validate_rad_ts_7(rad_path) -> None:
    # Sign has to be provided for all reaction coordinates or none of them. ValueError should be raised otherwise
    with pytest.raises(ValueError):
        ts_vibration.validate_transitionstate(rad_path, [[1, 16], [8, 9, 1]])
