import pathlib as pl

import pytest

from tcutility.analysis.task_specific.irc import _get_converged_molecules, concatenate_irc_trajectories
from tcutility.results.read import read
from tcutility.results.result import Result

#
current_dir = pl.Path(__file__).parent
ircs_dir = current_dir / "fixtures" / "irc_trajectories"


@pytest.fixture
def forward_irc() -> Result:
    return read(ircs_dir / "forward")


@pytest.fixture
def forward2_irc() -> Result:
    return read(ircs_dir / "forward_2")


@pytest.fixture
def backward_irc() -> Result:
    return read(ircs_dir / "backward")


@pytest.fixture
def backward2_irc() -> Result:
    return read(ircs_dir / "backward_2")


def test_len_irc_trajectories(forward_irc, forward2_irc, backward_irc, backward2_irc):
    res_objs = [forward_irc, forward2_irc, backward_irc, backward2_irc]

    expected_lengths = [84, 88, 91, 85]

    for expected_length, res_obj in zip(expected_lengths, res_objs):
        assert len(_get_converged_molecules(res_obj)) == expected_length


def test_len_final_trajectory(forward_irc, backward_irc, backward2_irc, forward2_irc):
    expected_lengths = [84, 91, 85, 88]

    concatenated_mols, _ = concatenate_irc_trajectories([forward_irc, backward_irc, backward2_irc, forward2_irc])
    assert len(concatenated_mols) == sum(expected_lengths) - 2  # 2 is the number of duplicated points in the concatenated trajectory. In this case, two seperate ircs are concatenated and so there are two duplicated points.

    concatenated_mols, _ = concatenate_irc_trajectories([forward_irc, backward_irc], reverse=True)
    assert len(concatenated_mols) == 84 + 91 - 1


if __name__ == "__main__":
    pytest.main()
