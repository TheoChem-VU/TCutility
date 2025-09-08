from tcutility.data import functionals


def test_get():
    assert functionals.get_functional("BLYP-D3(BJ)").name == "BLYP-D3(BJ)"
    assert functionals.get_functional("BLYP-D3(BJ)").path_safe_name == "BLYP-D3BJ"
    assert functionals.get_functional("BLYP-D3(BJ)").name_no_disp == "BLYP"
    assert functionals.get_functional("BLYP-D3(BJ)").category == "GGA"
    assert functionals.get_functional("BLYP-D3(BJ)").dispersion == "D3(BJ)"
    assert functionals.get_functional("BLYP-D3(BJ)").dispersion_name == "GRIMME3 BJDAMP"
    assert functionals.get_functional("BLYP-D3(BJ)").includes_disp is False
    assert functionals.get_functional("BLYP-D3(BJ)").use_libxc is False
    assert functionals.get_functional("BLYP-D3(BJ)").available_in_adf is True


def test_get2():
    assert functionals.get_functional("rev-DSD-PBEP86").name == "rev-DSD-PBEP86"
    assert functionals.get_functional("rev-DSD-PBEP86").name_no_disp == "rev-DSD-PBEP86"
    assert functionals.get_functional("rev-DSD-PBEP86").category == "DoubleHybrid"
    assert functionals.get_functional("rev-DSD-PBEP86").dispersion is None
    assert functionals.get_functional("rev-DSD-PBEP86").dispersion_name is None
    assert functionals.get_functional("rev-DSD-PBEP86").includes_disp is False
    assert functionals.get_functional("rev-DSD-PBEP86").use_libxc is False
    assert functionals.get_functional("rev-DSD-PBEP86").available_in_adf is True


def test_functional_name_from_path_safe_name():
    assert functionals.functional_name_from_path_safe_name("BLYPD3BJ") == "BLYP-D3(BJ)"


def test_functional_name_from_path_safe_name2():
    assert functionals.functional_name_from_path_safe_name("REVDSDPBEP86") == "rev-DSD-PBEP86"


def test_functional_name_from_path_safe_name3():
    for func, info in functionals.get_available_functionals().items():
        assert functionals.functional_name_from_path_safe_name(info.path_safe_name) == func


def test_functional_name_from_path_safe_name4():
    for func, info in functionals.get_available_functionals().items():
        assert functionals.functional_name_from_path_safe_name(info.path_safe_name.replace("-", "")) == func


if __name__ == "__main__":
    import pytest

    pytest.main()
