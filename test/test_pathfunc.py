from tcutility import pathfunc


def test_split_all():
	assert pathfunc.split_all('a/b/c') == ['a', 'b', 'c']


def test_split_all2():
	assert pathfunc.split_all('a') == ['a']


def test_split_all3():
	assert pathfunc.split_all('') == ['']


def test_split_all4():
	import os
	assert pathfunc.split_all(os.path.join('a', 'b', 'c')) == ['a', 'b', 'c']



if __name__ == '__main__':
	import pytest 

	pytest.main()
