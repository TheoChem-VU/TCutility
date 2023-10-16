from TCutility import results

def test_init():
	res = results.result.Result()


def test_assign_simple():
	res = results.result.Result()
	res.a = 10
	assert res.a == 10


def test_contains():
	res = results.result.Result()
	res.a = 10
	assert 'a' in res


def test_contains2():
	res = results.result.Result()
	res.a.b = 10
	assert 'a' in res


def test_contains3():
	res = results.result.Result()
	res.a.b = 10
	assert 'b' in res.a


def test_contains_neg():
	res = results.result.Result()
	assert 'a' not in res


def test_contains_neg2():
	res = results.result.Result()
	assert 'b' not in res.a


def test_contains_neg3():
	res = results.result.Result()
	res.a.b = 10
	assert 'b' not in res


def test_contains_neg4():
	res = results.result.Result()
	res.a
	assert 'a' not in res
