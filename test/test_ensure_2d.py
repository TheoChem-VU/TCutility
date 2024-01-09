from TCutility import ensure_2d


def test_0d_1():
    assert ensure_2d(5) == [[5]]


def test_0d_2():
    assert ensure_2d(None) == [[None]]


def test_0d_3():
    assert ensure_2d("abcdefghijklmnopqrstuvwxyz") == [["abcdefghijklmnopqrstuvwxyz"]]


def test_1d_1():
    assert ensure_2d([5]) == [[5]]


def test_1d_2():
    assert ensure_2d([None]) == [[None]]


def test_1d_3():
    assert ensure_2d(["abcdefghijklmnopqrstuvwxyz"]) == [["abcdefghijklmnopqrstuvwxyz"]]


def test_1d_4():
    assert ensure_2d([1, 2, 3, 4, 5]) == [[1], [2], [3], [4], [5]]


def test_1d_5():
    assert ensure_2d((1, 2, 3, 4, 5)) == [[1], [2], [3], [4], [5]]


def test_1d_6():
    assert ensure_2d({1, 2, 3, 4, 5}) == [[1], [2], [3], [4], [5]]


def test_1d_7():
    assert ensure_2d([1, 2, 3, 4, 5], transposed=True) == [[1, 2, 3, 4, 5]]


def test_1d_8():
    assert ensure_2d((1, 2, 3, 4, 5), transposed=True) == [[1, 2, 3, 4, 5]]


def test_1d_9():
    assert ensure_2d({1, 2, 3, 4, 5}, transposed=True) == [[1, 2, 3, 4, 5]]


def test_2d_1():
    assert ensure_2d([[1, 2, 3, 4, 5]]) == [[1, 2, 3, 4, 5]]


def test_2d_2():
    assert ensure_2d(((1, 2, 3, 4, 5),)) == [[1, 2, 3, 4, 5]]


def test_2d_3():
    assert ensure_2d([{1, 2, 3, 4, 5}]) == [[1, 2, 3, 4, 5]]


def test_2d_4():
    assert ensure_2d([[1, 2, 3, 4, 5]], transposed=True) == [[1, 2, 3, 4, 5]]


def test_2d_5():
    assert ensure_2d(((1, 2, 3, 4, 5),), transposed=True) == [[1, 2, 3, 4, 5]]


def test_2d_6():
    assert ensure_2d([{1, 2, 3, 4, 5}], transposed=True) == [[1, 2, 3, 4, 5]]


if __name__ == "__main__":
    import pytest

    pytest.main()
