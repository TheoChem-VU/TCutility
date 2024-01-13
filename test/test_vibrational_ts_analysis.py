from tcutility import results
from tcutility.analysis import ts_vibration
import pytest
import numpy as np
import os

j = os.path.join


def test_sn2_determine_rc() -> None:
    result = results.read(j(os.path.split(__file__)[0], "fixtures", "chloromethane_sn2_ts"))
    assert np.array_equal(ts_vibration.determine_ts_reactioncoordinate(result), np.array([[1, 2, 1], [1, 6, -1]]))


def test_rad_determine_rc_1() -> None:
    result = results.read(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"))
    assert np.array_equal(ts_vibration.determine_ts_reactioncoordinate(result, min_delta_dist=0.1), np.array([[1, 16, -1]]))


def test_rad_determine_rc_2() -> None:
    result = results.read(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"))
    assert np.array_equal(ts_vibration.determine_ts_reactioncoordinate(result, min_delta_dist=0.0), np.array([[1, 2, 1], [1, 8, 1], [1, 16, -1], [8, 9, -1]]))


def test_validate_sn2_ts_1() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "chloromethane_sn2_ts"), [[1, 2, 1], [1, 6, -1]])
    assert result is True


def test_validate_sn2_ts_2() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "chloromethane_sn2_ts"), [[2, 3, 1], [1, 6, -1]])
    assert result is False  # [2,3,1] should not be present


def test_validate_rad_ts_1() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"))
    assert result is True


def test_validate_rad_ts_2() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"), [1, 16, 1], min_delta_dist=0.1)
    assert result is True


def test_validate_rad_ts_3() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"), [[9, 8, -3], [16, 1, -5]], min_delta_dist=0.0)
    assert result is True  # Testing user input normalization


def test_validate_rad_ts_4() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"), [1, 16])
    assert result is True


def test_validate_rad_ts_5() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"), [8, 9, 1], min_delta_dist=0.1)
    assert result is False  # Should not be present with this min_delta_dist parameter value


def test_validate_rad_ts_6() -> None:
    result = ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"), [[1, 16, 1], [8, 9, -1]])
    assert result is False  # Should have equal signs


def test_validate_rad_ts_7() -> None:
    # Sign has to be provided for all reaction coordinates or none of them. ValueError should be raised otherwise
    with pytest.raises(ValueError):
        ts_vibration.validate_transitionstate(j(os.path.split(__file__)[0], "fixtures", "radical_addition_ts"), [[1, 16], [8, 9, 1]])
