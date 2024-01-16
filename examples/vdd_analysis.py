import pathlib as pl
import tcutility.results as results
from tcutility.analysis.vdd import manager


DIRS = {0: "fa_acid_amide_cs", 1: "fa_squaramide_se_cs", 2: "fa_donor_acceptor_nosym", 3: "geo_nosym"}


def main():
    output_dir = pl.Path(__file__).parent
    test_dir = output_dir.parent / "test" / "fixtures" / "VDD"
    # test_dir = test_dir / DIRS[2]
    # calc_res = results.read(test_dir)
    # vdd_manager = manager.create_vdd_charge_manager(calc_res)
    # print(vdd_manager)
    # print(calc_res.properties.vdd.AA + calc_res.properties.vdd.AAA)

    # Multiple calculations
    calc_dirs = [test_dir / DIRS[i] for i in range(4)]
    calc_res = [results.read(calc_dir) for calc_dir in calc_dirs]
    vdd_managers = [manager.create_vdd_charge_manager(res) for res in calc_res]
    print(vdd_managers)
    manager.VDDChargeManager.write_to_txt(output_dir, vdd_managers)


if __name__ == "__main__":
    main()
