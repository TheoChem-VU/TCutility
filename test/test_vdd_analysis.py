import pytest
import pathlib as pl
from scm.plams import KFReader
import numpy as np
from tcutility.analysis.vdd import charge, manager
from tcutility.results import ams
from tcutility import results

# VDDCharge, manager.VDDChargeManager, get_vdd_charges, _get_fragment_indices_from_input_order

current_dir = pl.Path(__file__).parent
R_TOLERANCE = 1e-5  # relative tolerance for floating point comparisons


@pytest.fixture
def kfreader_fa_disordered_fragindices_cs():
    # replace 'your_file' with the path to your file
    return KFReader(str(current_dir / "fixtures" / "VDD" / "fa_acid_amide_cs" / "fa_acid_amide_cs.adf.rkf"))


@pytest.fixture
def kfreader_fa_ordered_fragindices_cs():
    return KFReader(str(current_dir / "fixtures" / "VDD" / "fa_squaramide_se_cs" / "fa_squaramide_se_cs.adf.rkf"))


@pytest.fixture
def vdd_manager_fa_nosym():
    fa_results = results.read(current_dir / "fixtures" / "VDD" / "fa_donor_acceptor_nosym")
    return manager.create_vdd_charge_manager(fa_results)


@pytest.fixture
def kfreader_geo_nosym():
    return KFReader(str(current_dir / "fixtures" / "VDD" / "geo_nosym" / "geo_nosym.adf.rkf"))


# ----------------------------------------------------------
# ------------------ get_fragment_indices ------------------
# ----------------------------------------------------------


def test_get_fragment_indices_from_input_order_disordered(kfreader_fa_disordered_fragindices_cs):
    frag_indices = ams._get_fragment_indices_from_input_order(kfreader_fa_disordered_fragindices_cs)
    assert np.array_equal(frag_indices, np.array([1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1]))


def test_get_fragment_indices_from_input_order_ordered(kfreader_fa_ordered_fragindices_cs):
    frag_indices = ams._get_fragment_indices_from_input_order(kfreader_fa_ordered_fragindices_cs)
    assert np.array_equal(frag_indices, np.array([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2]))


# ----------------------------------------------------------
# --------------- manager.VDDChargeManager -----------------
# ----------------------------------------------------------


# def test_get_vdd_charges_irrep_cs(kfreader_fa_ordered_fragindices_cs):
#     vdd_charges = get_vdd_charges(kfreader_fa_ordered_fragindices_cs)

#     assert len(vdd_charges) == 3, "More than three irreps found in the returned dict"
#     assert "vdd" in vdd_charges, "'vdd' not found in the returned dict"
#     assert "AA" in vdd_charges, "'AA' not found in the returned dict"
#     assert "AAA" in vdd_charges, "'AAA' not found in the returned dict"


# def test_get_vdd_charges_irrep_nosym(kfreader_fa_nosym):
#     vdd_charges = get_vdd_charges(kfreader_fa_nosym)

#     assert "vdd" in vdd_charges, "'vdd' not found in the returned dict"
#     assert len(vdd_charges) == 1, "More than one irrep found in the returned dict"


# def test_get_vdd_charges_charge_values_fa_cs(kfreader_fa_ordered_fragindices_cs):
#     vdd_charges = get_vdd_charges(kfreader_fa_ordered_fragindices_cs)

#     # The "/1000" is because the charges are in [electrons] in the kf file but it is more readable to use [millielectrons] here
#     test_charge_1 = charge.VDDCharge(atom_index=1, atom_symbol="C", charge=-39.753 / 1000, frag_index=1)
#     test_charge_2 = charge.VDDCharge(atom_index=2, atom_symbol="Se", charge=-164.520 / 1000, frag_index=1)
#     test_charge_3 = charge.VDDCharge(atom_index=8, atom_symbol="H", charge=53.397 / 1000, frag_index=2)
#     assert vdd_charges["vdd"][0] == test_charge_1, "Charge values are not as expected"
#     assert vdd_charges["vdd"][1] == test_charge_2, "Charge values are not as expected"
#     assert vdd_charges["vdd"][7] == test_charge_3, "Charge values are not as expected"
#     assert np.isclose(np.sum([charge.charge for charge in vdd_charges["vdd"]]), 0.0, atol=1e-1), "Total charge is not zero"


def test_get_vdd_charges_charge_values_geo_nosym(vdd_manager_fa_nosym: manager.VDDChargeManager):
    vdd_charges = vdd_manager_fa_nosym.get_vdd_charges("e")

    # The "/1000" is because the charges are in [electrons] in the kf file but it is more readable to use [millielectrons] here
    test_charge_1 = charge.VDDCharge(atom_index=3, atom_symbol="C", charge=-0.329 / 1000, frag_index=1)
    test_charge_2 = charge.VDDCharge(atom_index=4, atom_symbol="C", charge=-0.403 / 1000, frag_index=1)
    test_charge_3 = charge.VDDCharge(atom_index=12, atom_symbol="O", charge=-1.210 / 1000, frag_index=2)
    assert vdd_charges["vdd"][2] == test_charge_1, "Charge values are not as expected"
    assert vdd_charges["vdd"][3] == test_charge_2, "Charge values are not as expected"
    assert vdd_charges["vdd"][11] == test_charge_3, "Charge values are not as expected"
    assert np.isclose(np.sum([charge.charge for charge in vdd_charges["vdd"]]), 0.0, atol=1e-1), "Total charge is not zero"


# def test_get_vdd_charges_irrep_sum_cs(kfreader_fa_ordered_fragindices_cs):
#     vdd_charges = get_vdd_charges(kfreader_fa_ordered_fragindices_cs)

#     vdd_charge = vdd_charges["vdd"][0].charge
#     aa_charge = vdd_charges["AA"][0].charge
#     aaa_charge = vdd_charges["AAA"][0].charge
#     assert np.isclose(vdd_charge, aa_charge + aaa_charge, rtol=R_TOLERANCE), "Total charge is not the sum of the irreps"


# def test_summed_charges(kfreader_fa_ordered_fragindices_cs):
#     vdd_charges = get_vdd_charges(kfreader_fa_ordered_fragindices_cs)
#     charge_manager = manager.VDDChargeManager(vdd_charges=vdd_charges)
#     summed_charges = charge_manager.get_summed_vdd_charges()

#     assert len(summed_charges.keys()) == 3, "More than three irreps found in the summed charges"
#     assert "AA" in summed_charges, "'AA' not found in the summed charges"
#     assert "AAA" in summed_charges, "'AAA' not found in the summed charges"
#     assert "vdd" in summed_charges, "'vdd' not found in the summed charges"

#     frag1_total = summed_charges["vdd"]["1"]
#     frag2_total = summed_charges["vdd"]["2"]
#     frag1_aa = summed_charges["AA"]["1"]
#     frag1_aaa = summed_charges["AAA"]["1"]
#     assert np.isclose(frag1_total, -357.106, rtol=1e-5), "Summed charges total are not as expected"
#     assert np.isclose(frag1_aa, 163.7488, rtol=1e-5), "Summed charges AA are not as expected"
#     assert np.isclose(frag1_aaa, -520.8548, rtol=1e-5), "Summed charges AAA are not as expected"

#     assert np.isclose(frag1_total, frag1_aa + frag1_aaa, atol=1e-2), "Total charge is not the sum of the irreps"
#     assert np.isclose(frag1_total + frag2_total, 0, atol=1e-1), "Total charge is not the sum of the irreps"


def test_summed_charges_nosym(vdd_manager_fa_nosym: manager.VDDChargeManager):
    summed_charges = vdd_manager_fa_nosym.get_summed_vdd_charges()

    assert len(summed_charges.keys()) == 1, "Irreps found in the summed charges for nosym calculation"
