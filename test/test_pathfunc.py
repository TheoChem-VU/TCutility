import os
import tempfile

import pytest
from tcutility import pathfunc


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories
        os.makedirs(os.path.join(temp_dir, "subdir_a", "subsubdir_b"))
        os.makedirs(os.path.join(temp_dir, "subdir_a", "subsubdir_c"))
        os.makedirs(os.path.join(temp_dir, "subdir_b"))
        os.makedirs(os.path.join(temp_dir, "subdir_c"))
        yield temp_dir


def test_split_dir_structure(temp_dir):
    raise NotImplementedError


def test_split_all():
    assert pathfunc.split_all("a/b/c") == ["a", "b", "c"]


def test_split_all2():
    assert pathfunc.split_all("a") == ["a"]


def test_split_all3():
    assert pathfunc.split_all("") == [""]


def test_split_all4():
    import os

    assert pathfunc.split_all(os.path.join("a", "b", "c")) == ["a", "b", "c"]


if __name__ == "__main__":
    import pytest

    pytest.main()
