import pathlib as pl

import numpy as np
import pytest
from scm.plams import KFReader
from tcutility import results
from tcutility.analysis.vdd import charge, manager
from tcutility.results import ams

# VDDCharge, manager.VDDChargeManager, get_vdd_charges, _get_fragment_indices_from_input_order

current_dir = pl.Path(__file__).parent
R_TOLERANCE = 1e-5  # relative tolerance for floating point comparisons


@pytest.fixture
def kfreader_fa_disordered_fragindices_cs():
    # replace 'your_file' with the path to your file
    return KFReader(str(current_dir / "fixtures" / "VDD" / "fa_acid_amide_cs" / "fa_acid_amide_cs.adf.rkf"))


@pytest.fixture
def vdd_manager_fa_disordered_fragindices_cs():
    fa_results = results.read(current_dir / "fixtures" / "VDD" / "fa_acid_amide_cs")
    return manager.create_vdd_charge_manager(fa_results)


@pytest.fixture
def kfreader_fa_ordered_fragindices_cs():
    return KFReader(str(current_dir / "fixtures" / "VDD" / "fa_squaramide_se_cs" / "fa_squaramide_se_cs.adf.rkf"))


@pytest.fixture
def vdd_manager_fa_ordered_fragindices_cs():
    fa_results = results.read(current_dir / "fixtures" / "VDD" / "fa_squaramide_se_cs")
    return manager.create_vdd_charge_manager(fa_results)


@pytest.fixture
def kfreader_fa_nosym():
    return KFReader(str(current_dir / "fixtures" / "VDD" / "fa_donor_acceptor_nosym" / "fa_donor_acceptor_nosym.adf.rkf"))


@pytest.fixture
def vdd_manager_fa_nosym():
    fa_results = results.read(current_dir / "fixtures" / "VDD" / "fa_donor_acceptor_nosym")
    return manager.create_vdd_charge_manager(fa_results)


@pytest.fixture
def kfreader_geo_nosym():
    return KFReader(str(current_dir / "fixtures" / "VDD" / "geo_nosym" / "geo_nosym.adf.rkf"))


@pytest.fixture
def vdd_manager_geo_nosym():
    geo_results = results.read(current_dir / "fixtures" / "VDD" / "geo_nosym" / "geo_nosym.adf.rkf")
    return manager.create_vdd_charge_manager(geo_results)


# ----------------------------------------------------------
# ------------------ get_fragment_indices ------------------
# ----------------------------------------------------------


def test_get_fragment_indices_from_input_order_disordered(kfreader_fa_disordered_fragindices_cs):
    frag_indices = ams._get_fragment_indices_from_input_order(kfreader_fa_disordered_fragindices_cs)
    assert np.array_equal(frag_indices, np.array([1, 1, 1, 2, 2, 2, 1, 1, 2, 2, 2]))


def test_get_fragment_indices_from_input_order_ordered(kfreader_fa_ordered_fragindices_cs):
    frag_indices = ams._get_fragment_indices_from_input_order(kfreader_fa_ordered_fragindices_cs)
    assert np.array_equal(frag_indices, np.array([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2]))


# ----------------------------------------------------------
# --------------- manager.VDDChargeManager -----------------
# ----------------------------------------------------------


def test_change_unit(vdd_manager_fa_ordered_fragindices_cs: manager.VDDChargeManager):
    manager = vdd_manager_fa_ordered_fragindices_cs
    initial_charges = manager.get_vdd_charges("e")
    manager.change_unit("e")
    manager.change_unit("me")
    manager.change_unit("me")
    manager.change_unit("e")
    manager.change_unit("me")
    second_charges = manager.get_vdd_charges("e")
    other_unit_charges = manager.get_vdd_charges("me")

    assert np.allclose([charge.charge for charge in initial_charges["vdd"]], [charge.charge for charge in second_charges["vdd"]]), "Charges are not the same after changing units"
    assert np.allclose([charge.charge for charge in initial_charges["vdd"]], [charge.charge / 1000 for charge in other_unit_charges["vdd"]])


def test_get_vdd_charges_irrep_cs(vdd_manager_fa_ordered_fragindices_cs: manager.VDDChargeManager):
    vdd_charges = vdd_manager_fa_ordered_fragindices_cs.get_vdd_charges("e")

    assert len(vdd_charges) == 3, "More than three irreps found in the returned dict"
    assert "vdd" in vdd_charges, "'vdd' not found in the returned dict"
    assert "AA" in vdd_charges, "'AA' not found in the returned dict"
    assert "AAA" in vdd_charges, "'AAA' not found in the returned dict"


def test_get_vdd_charges_irrep_nosym(vdd_manager_fa_nosym: manager.VDDChargeManager):
    vdd_charges = vdd_manager_fa_nosym.get_vdd_charges("e")

    assert "vdd" in vdd_charges, "'vdd' not found in the returned dict"
    assert len(vdd_charges) == 1, "More than one irrep found in the returned dict"


def test_get_vdd_charges_charge_values_fa_cs(vdd_manager_fa_ordered_fragindices_cs: manager.VDDChargeManager):
    vdd_charges = vdd_manager_fa_ordered_fragindices_cs.get_vdd_charges("e")

    # The "/1000" is because the charges are in [electrons] in the kf file but it is more readable to use [millielectrons] here
    test_charge_1 = charge.VDDCharge(atom_index=1, atom_symbol="C", charge=-39.75281 / 1000, frag_index=1)
    test_charge_2 = charge.VDDCharge(atom_index=2, atom_symbol="Se", charge=-164.520 / 1000, frag_index=1)
    test_charge_3 = charge.VDDCharge(atom_index=8, atom_symbol="H", charge=53.397 / 1000, frag_index=2)
    assert np.isclose(vdd_charges["vdd"][0].charge, test_charge_1.charge), "Charge values are not as expected"
    assert np.isclose(vdd_charges["vdd"][1].charge, test_charge_2.charge), "Charge values are not as expected"
    assert np.isclose(vdd_charges["vdd"][7].charge, test_charge_3.charge), "Charge values are not as expected"
    assert np.isclose(np.sum([charge.charge for charge in vdd_charges["vdd"]]), 0.0, atol=1e-1), "Total charge is not zero"


def test_get_vdd_charges_charge_values_geo_nosym(vdd_manager_fa_nosym: manager.VDDChargeManager):
    vdd_charges = vdd_manager_fa_nosym.get_vdd_charges("e")

    # The "/1000" is because the charges are in [electrons] in the kf file but it is more readable to use [millielectrons] here
    test_charge_1 = charge.VDDCharge(atom_index=3, atom_symbol="C", charge=-0.328746 / 1000, frag_index=1)
    test_charge_2 = charge.VDDCharge(atom_index=4, atom_symbol="C", charge=-0.40333031 / 1000, frag_index=1)
    test_charge_3 = charge.VDDCharge(atom_index=12, atom_symbol="O", charge=-1.210724 / 1000, frag_index=2)
    assert np.isclose(vdd_charges["vdd"][2].charge, test_charge_1.charge), "Charge values are not as expected"
    assert np.isclose(vdd_charges["vdd"][3].charge, test_charge_2.charge), "Charge values are not as expected"
    assert np.isclose(vdd_charges["vdd"][11].charge, test_charge_3.charge), "Charge values are not as expected"
    assert np.isclose(np.sum([charge.charge for charge in vdd_charges["vdd"]]), 0.0, atol=1e-1), "Total charge is not zero"


def test_get_vdd_charges_irrep_atom_sum_cs(vdd_manager_fa_ordered_fragindices_cs: manager.VDDChargeManager):
    vdd_charges = vdd_manager_fa_ordered_fragindices_cs.get_vdd_charges("e")

    vdd_charge = vdd_charges["vdd"][0].charge
    aa_charge = vdd_charges["AA"][0].charge
    aaa_charge = vdd_charges["AAA"][0].charge
    assert np.isclose(vdd_charge, aa_charge + aaa_charge, rtol=R_TOLERANCE), "Total atom charge is not the sum of the irreps"


def test_summed_charges(vdd_manager_fa_ordered_fragindices_cs: manager.VDDChargeManager):
    summed_charges = vdd_manager_fa_ordered_fragindices_cs.get_summed_vdd_charges()  # in unit [me]

    assert len(summed_charges.keys()) == 3, "More than three irreps found in the summed charges"
    assert "AA" in summed_charges, "'AA' not found in the summed charges"
    assert "AAA" in summed_charges, "'AAA' not found in the summed charges"
    assert "vdd" in summed_charges, "'vdd' not found in the summed charges"

    frag1_total = summed_charges["vdd"]["1"]
    frag2_total = summed_charges["vdd"]["2"]
    frag1_aa = summed_charges["AA"]["1"]
    frag1_aaa = summed_charges["AAA"]["1"]
    assert np.isclose(frag1_total, -357.106, rtol=1e-5), "Summed charges total are not as expected"
    assert np.isclose(frag1_aa, 163.7488, rtol=1e-5), "Summed charges AA are not as expected"
    assert np.isclose(frag1_aaa, -520.8548, rtol=1e-5), "Summed charges AAA are not as expected"

    assert np.isclose(frag1_total, frag1_aa + frag1_aaa, atol=1e-2), "Total charge is not the sum of the irreps"
    assert np.isclose(frag1_total + frag2_total, 0, atol=1e-1), "Total charge is not the sum of the irreps"


def test_summed_charges_nosym(vdd_manager_fa_nosym: manager.VDDChargeManager):
    summed_charges = vdd_manager_fa_nosym.get_summed_vdd_charges()

    assert len(summed_charges.keys()) == 1, "Irreps found in the summed charges for nosym calculation"
