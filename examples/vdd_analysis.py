import pathlib as pl

import tcutility.results as results
from tcutility.analysis.vdd import manager

DIRS = {0: "fa_acid_amide_cs", 1: "fa_squaramide_se_cs", 2: "fa_donor_acceptor_nosym", 3: "geo_nosym"}


def main():
    output_dir = pl.Path(__file__).parent
    base_dir = output_dir.parent / "test" / "fixtures" / "VDD"
    calc_dir = base_dir / DIRS[1]
    calc_res = results.read(calc_dir)
    vdd_manager = manager.create_vdd_charge_manager(name=calc_dir.name, results=calc_res)

    # Print the VDD charges to standard output
    print(vdd_manager)

    # Change the unit of the VDD charges to mili-electrons
    vdd_manager.change_unit("e")
    print(vdd_manager)
    vdd_manager.change_unit("me")

    # The program checks automatically if the calculation is a fragment calculation and prints the summed VDD charges if it is
    # You can check by yourself if the calculation is a fragment calculation
    is_fragment_calculation = vdd_manager.is_fragment_calculation
    print(is_fragment_calculation)

    # Write the VDD charges to a text file (static method because multiple managers can be written to the same file)
    manager.VDDChargeManager.write_to_txt(output_dir, vdd_manager)

    # Plot the VDD charges per atom in a bar graph
    vdd_manager.plot_vdd_charges_per_atom(output_dir)

    # Write the VDD charges to an excel file
    vdd_manager.write_to_excel(output_dir)

    # Multiple calculations can be combined into a single file
    # calc_dirs = [base_dir / calc for calc in DIRS.values()]
    # calc_res = [results.read(calc_dir) for calc_dir in calc_dirs]
    # vdd_managers = [manager.create_vdd_charge_manager(name=calc_dir.name, results=res) for calc_dir, res in zip(calc_dirs, calc_res)]

    # Plot the VDD charges per atom in a bar graph
    # [vdd_manager.plot_vdd_charges_per_atom(output_dir) for vdd_manager in vdd_managers]

    # Write the VDD charges to a text file
    # manager.VDDChargeManager.write_to_txt(output_dir, vdd_managers)


if __name__ == "__main__":
    main()
