from TCutility import log


def test_log(capfd):
    log.print_date = True
    log.tab_level = 0
    log.log('test, test')
    out, err = capfd.readouterr()
    assert out.strip()[22:] == 'test, test'  # first 22 caracters are the timestamp, we also remove newline and carriage returns with strip()


def test_log_tab_level(capfd):
    log.print_date = True
    log.tab_level = 3
    log.log('test, test')
    out, err = capfd.readouterr()
    assert out.strip()[22:] == '\t\t\ttest, test'


def test_log_no_timestamp(capfd):
    log.print_date = False
    log.tab_level = 0
    log.log('test, test')
    out, err = capfd.readouterr()
    assert out.strip() == 'test, test'


if __name__ == '__main__':
    import pytest
    pytest.main()
