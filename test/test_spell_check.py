from tcutility import spell_check


def test_wagner_fischer1():
    dist = spell_check.wagner_fischer('kitten', 'sitting')
    assert dist == 3

def test_wagner_fischer2():
    dist = spell_check.wagner_fischer('kitten', 'kitten')
    assert dist == 0

def test_wagner_fischer3():
    dist = spell_check.wagner_fischer('kitten', 'Kitten')
    assert dist == 1

def test_wagner_fischer4():
    dist = spell_check.wagner_fischer('kitten', 'Kitten', case_missmatch_cost=.5)
    assert dist == .5

def test_wagner_fischer5():
    dist = spell_check.wagner_fischer('kitten', 'sitting', case_missmatch_cost=.5)
    assert dist == 3

def test_wagner_fischer6():
    dist = spell_check.wagner_fischer('kitten', 'Kitten', substitution_cost=.5)
    assert dist == 1

def test_wagner_fischer7():
    dist = spell_check.wagner_fischer('kitten', 'sittin', substitution_cost=.5)
    assert dist == 1

def test_wagner_fischer8():
    dist = spell_check.wagner_fischer('kitten', 'kittttten', insertion_cost=.5)
    assert dist == 1.5

def test_get_closest1():
    closest = spell_check.get_closest('kitten', ['mitten', 'bitten', 'sitting'])
    assert closest == ['mitten', 'bitten']

def test_get_closest2():
    closest = spell_check.get_closest('kitten', ['mitten', 'bitten', 'sitting'], compare_func=spell_check.naive_recursive)
    assert closest == ['mitten', 'bitten']

def test_get_closest3():
    closest = spell_check.get_closest('kitten', ['mitten', 'bitten', 'sitting'], ignore_chars='ening')
    assert closest == ['mitten', 'bitten', 'sitting']

def test_get_closest4():
    closest = spell_check.get_closest('kitten', ['Kitten', 'kItten', 'kiTten', 'KItten', 'KITten'], ignore_case=False)
    assert closest == ['Kitten', 'kItten', 'kiTten']

def test_get_closest5():
    closest = spell_check.get_closest('kitten', ['Kitten', 'kItten', 'kiTten', 'KItten', 'KITten', 'KITTEN'], ignore_case=True)
    assert closest == ['Kitten', 'kItten', 'kiTten', 'KItten', 'KITten', 'KITTEN']

def test_get_closest6():
    closest = spell_check.get_closest('kitten', ['Kitten', 'kItten', 'kiTten', 'KItten', 'KITten', 'KITTEN'], maximum_distance=2)
    assert closest == ['Kitten', 'kItten', 'kiTten', 'KItten']

if __name__ == '__main__':
    import pytest

    pytest.main()
