import pathlib as pl

from tcutility.analysis.vdd.manager import VDDChargeManager, create_vdd_charge_manager
from tcutility.results.read import read

DIRS = {0: "fa_acid_amide_cs", 1: "fa_squaramide_se_cs", 2: "fa_donor_acceptor_nosym", 3: "geo_nosym"}


def main():
    output_dir = pl.Path(__file__).parent
    base_dir = output_dir.parent / "test" / "fixtures" / "VDD"
    calc_dir = base_dir / DIRS[1]
    calc_res = read(calc_dir)
    vdd_manager = create_vdd_charge_manager(results=calc_res)

    # Print the VDD charges to standard output
    print(vdd_manager)

    # Change the unit of the VDD charges to mili-electrons
    vdd_manager.change_unit("e")
    # print(vdd_manager)
    vdd_manager.change_unit("me")

    # The program checks automatically if the calculation is a fragment calculation and prints the summed VDD charges if it is
    # You can check by yourself if the calculation is a fragment calculation
    is_fragment_calculation = vdd_manager.is_fragment_calculation
    print(is_fragment_calculation)

    # Write the VDD charges to a text file (static method because multiple managers can be written to the same file)
    VDDChargeManager.write_to_txt(output_dir, vdd_manager)

    # Plot the VDD charges per atom in a bar graph
    vdd_manager.plot_vdd_charges_per_atom(output_file=output_dir / "vdd_charges.png")

    # Write the VDD charges to an excel file
    vdd_manager.write_to_excel(output_file=output_dir / "vdd_charges.xlsx")

    # Multiple calculations can be combined into a single file
    calc_dirs = [base_dir / calc for calc in DIRS.values()]
    calc_res = [read(calc_dir) for calc_dir in calc_dirs]
    vdd_managers = [create_vdd_charge_manager(results=res) for res in calc_res]

    # Plot the VDD charges per atom in a bar graph
    [vdd_manager.plot_vdd_charges_per_atom(output_dir / vdd_manager.name) for vdd_manager in vdd_managers]

    # Write the VDD charges to a text file
    VDDChargeManager.write_to_txt(output_dir, vdd_managers)


if __name__ == "__main__":
    main()
