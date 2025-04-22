import os
import tempfile
import pytest
from tcutility import pathfunc


@pytest.fixture
def temp_dir():
    '''
    This will create a directory structure like:

    root
    |- subdir_a
    |  |- subsubdir_b
    |  |- subsubdir_c
    |- subdir_b
    |- subdir_c
    '''
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories
        os.makedirs(os.path.join(temp_dir, "subdir_a", "subsubdir_b"))
        os.makedirs(os.path.join(temp_dir, "subdir_a", "subsubdir_c"))
        os.makedirs(os.path.join(temp_dir, "subdir_b"))
        os.makedirs(os.path.join(temp_dir, "subdir_c"))
        yield temp_dir

@pytest.fixture
def temp_dir2():
    '''
    This will create a directory structure like:

    root
    |- NH3-BH3
    |   |- BLYP_QZ4P
    |   |  |- extra_dir
    |   |  |- blablabla
    |   |
    |   |- BLYP_TZ2P
    |   |  |- another_dir
    |   |
    |   |- M06-2X_TZ2P
    |
    |- SN2
    |   |- BLYP_TZ2P
    |   |- M06-2X_TZ2P
    |   |  |- M06-2X_TZ2P
    '''
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories
        os.makedirs(os.path.join(temp_dir, "NH3-BH3", "BLYP_QZ4P", "extra_dir"))
        os.makedirs(os.path.join(temp_dir, "NH3-BH3", "BLYP_QZ4P", "blablabla"))
        os.makedirs(os.path.join(temp_dir, "NH3-BH3", "BLYP_TZ2P", "another_dir"))
        os.makedirs(os.path.join(temp_dir, "NH3-BH3", "M06-2X_TZ2P"))
        os.makedirs(os.path.join(temp_dir, "SN2", "BLYP_TZ2P"))
        os.makedirs(os.path.join(temp_dir, "SN2", "M06-2X_TZ2P", "M06-2X_TZ2P"))
        yield temp_dir


def test_get_subdirectories(temp_dir):
    expected = {
        f'{temp_dir}/subdir_a/subsubdir_b',
        f'{temp_dir}/subdir_a/subsubdir_c',
        f'{temp_dir}/subdir_b',
        f'{temp_dir}/subdir_c'
    }
    assert sorted(pathfunc.get_subdirectories(temp_dir)) == sorted(expected)


def test_get_subdirectories2(temp_dir):
    expected = {
        f'{temp_dir}',
        f'{temp_dir}/subdir_a',
        f'{temp_dir}/subdir_a/subsubdir_b',
        f'{temp_dir}/subdir_a/subsubdir_c',
        f'{temp_dir}/subdir_b',
        f'{temp_dir}/subdir_c'
    }
    assert sorted(pathfunc.get_subdirectories(temp_dir, include_intermediates=True)) == sorted(expected)


def test_match(temp_dir2):
    assert len(pathfunc.match(temp_dir2, '{system}/{functional}_{basis_set}')) == 5


def test_match2(temp_dir2):
    matches = pathfunc.match(temp_dir2, '{system}/{functional}_{basis_set}')
    assert f"{temp_dir2}/SN2/M06-2X_TZ2P" in matches
    assert matches[f"{temp_dir2}/SN2/M06-2X_TZ2P"].system == 'SN2'
    assert matches[f"{temp_dir2}/SN2/M06-2X_TZ2P"].functional == 'M06-2X'
    assert matches[f"{temp_dir2}/SN2/M06-2X_TZ2P"].basis_set == 'TZ2P'


def test_split_all():
    assert pathfunc.split_all("a/b/c") == ["a", "b", "c"]


def test_split_all2():
    assert pathfunc.split_all("a") == ["a"]


def test_split_all3():
    # empty string corresponds to the `.` directory, i.e. here
    assert pathfunc.split_all("") == ["."]


def test_split_all4():
    import os

    assert pathfunc.split_all(os.path.join("a", "b", "c")) == ["a", "b", "c"]


def test_path_depth():
    assert pathfunc.path_depth('a/b/c') == 3


def test_path_depth2():
    assert pathfunc.path_depth('a/One Drive/c') == 3
    
def test_path_depth4():
    assert pathfunc.path_depth('a') == 1
    


if __name__ == "__main__":
    import pytest

    pytest.main(['-vv'])
