import pathlib as pl
import tcutility.results as results
from tcutility.analysis.vdd import manager
# from vucalc.printing_and_writing.data_printing import write_vdd_charges_per_atom, write_vdd_charges_per_frag


DIRS = {0: "fa_acid_amide_cs", 1: "fa_squaramide_se_cs", 2: "fa_donor_acceptor_nosym", 3: "geo_nosym"}


def main():
    output_dir = pl.Path(__file__).parent
    test_dir = output_dir.parent / "test" / "fixtures" / "VDD"
    test_dir = test_dir / DIRS[2]
    calc_res = results.read(test_dir)
    charges = calc_res.properties.vdd.charges
    symbols = calc_res.molecule.atom_symbols
    vdd_manager = manager.create_vdd_charge_manager(calc_res)
    print(vdd_manager)
    # print(calc_res.properties.vdd.AA + calc_res.properties.vdd.AAA)


if __name__ == "__main__":
    main()
