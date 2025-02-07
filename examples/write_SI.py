import pathlib as pl

from tcutility import formula
from tcutility.report.report import SI


def write_xyz_SI():
    # pwd = pl.Path(__file__).parent
    # with SI("test.docx") as si:
    #     si.add_heading("Test molecules:")
    #     si.add_xyz(str(pwd.parent / "test" / "fixtures" / "level_of_theory" / "M06_2X"), "Cyclo-octatriene")
    #     si.add_xyz(str(pwd.parent / "test" / "fixtures" / "ethanol"), formula.molecule("C2H5OH"))

    pwd = pl.Path("/scistor/tc/sle337/Promotie/VS_Collab/conformers/calculations/geo/anion_binding_different_radii")
    with SI(pwd / "test.docx", True) as si:
        si.add_heading("Test molecules:")
        folders = pwd.glob("*")

        for folder in folders:
            print(f"Adding xyz of {folder.name} to the SI")
            si.add_xyz(folder, folder.name)
    print(f"Done writing SI to {pwd / 'test.docx'}")


def make_main_energy_table(table):
    table.caption = f"Reaction barriers (Δ<i>E</i><sup>‡</sup>) and reaction energies (Δ<i>E</i><sub>rxn</sub>) (in kcal mol<sup>–1</sup>) for the reaction of {formula.molecule('H2C=X + CH3*', 'html')} via C–addition and X–addition.<sup>a</sup>"
    table.add_column(formula.molecule("X", "html"))
    table.add_column_group("Δ<i>E</i><sup>‡</sup>", ["C-addition", "X-addition"])
    table.add_column_group("Δ<i>E</i><sub>rxn</sub>", ["C-addition", "X-addition"])

    # Sample data to replace the database
    sample_data = {
        "CH2": {"C": {"TS_energy": 10.0, "P_energy": -5.0}, "X": {"TS_energy": 15.0, "P_energy": -10.0}},
        "SiH2": {"C": {"TS_energy": 12.0, "P_energy": -6.0}, "X": {"TS_energy": 18.0, "P_energy": -12.0}},
        "GeH2": {"C": {"TS_energy": 14.0, "P_energy": -7.0}, "X": {"TS_energy": 20.0, "P_energy": -14.0}},
        "SnH2": {"C": {"TS_energy": 16.0, "P_energy": -8.0}, "X": {"TS_energy": 22.0, "P_energy": -16.0}},
        "NH": {"C": {"TS_energy": 8.0, "P_energy": -4.0}, "X": {"TS_energy": 13.0, "P_energy": -9.0}},
        "PH": {"C": {"TS_energy": 9.0, "P_energy": -4.5}, "X": {"TS_energy": 14.0, "P_energy": -9.5}},
        "AsH": {"C": {"TS_energy": 11.0, "P_energy": -5.5}, "X": {"TS_energy": 16.0, "P_energy": -10.5}},
        "SbH": {"C": {"TS_energy": 13.0, "P_energy": -6.5}, "X": {"TS_energy": 18.0, "P_energy": -11.5}},
        "O": {"C": {"TS_energy": 7.0, "P_energy": -3.5}, "X": {"TS_energy": 12.0, "P_energy": -8.5}},
        "S": {"C": {"TS_energy": 9.0, "P_energy": -4.5}, "X": {"TS_energy": 14.0, "P_energy": -9.5}},
        "Se": {"C": {"TS_energy": 11.0, "P_energy": -5.5}, "X": {"TS_energy": 16.0, "P_energy": -10.5}},
        "Te": {"C": {"TS_energy": 13.0, "P_energy": -6.5}, "X": {"TS_energy": 18.0, "P_energy": -11.5}},
    }

    Xs = ["CH2", "SiH2", "GeH2", "SnH2", "NH", "PH", "AsH", "SbH", "O", "S", "Se", "Te"]
    for X in Xs:
        if X == "CH2":
            table.add_header_row("Tetrels")
        if X == "NH":
            table.add_header_row("Pnictogens")
        if X == "O":
            table.add_header_row("Chalcogens")

        row = []
        row.append(formula.molecule(X, "html"))

        row_data_C = sample_data[X]["C"]
        Ets_C = row_data_C["TS_energy"]
        Ep_C = row_data_C["P_energy"]

        row_data_X = sample_data[X]["X"]
        Ets_X = row_data_X["TS_energy"]
        Ep_X = row_data_X["P_energy"]

        row.append(f"{Ets_C: .1f}")
        if Ets_X is not None:
            row.append(f"{Ets_X: .1f}")
        else:
            row.append("[b]")
        row.append(f"{Ep_C: .1f}")
        row.append(f"{Ep_X: .1f}")

        table.add_row(row)
        table.merge_cells(3, (2, 3))
        table.merge_cells(3, (5, 6))

    table.add_footnote("<sup>a</sup> Computed at the ZORA-UOLYP/TZ2P level of theory. <sup>b</sup> Non-existent: structure not found.")


def write_table_SI():
    pwd = pl.Path("/scistor/tc/sle337/Promotie/VS_Collab/conformers/calculations/geo/anion_binding_different_radii")
    with SI(pwd / "main_tables_figures.docx", overwrite=True) as si_doc:
        si_doc.add_toc()
        si_doc.add_page_break()

        with si_doc.add_table() as table:
            make_main_energy_table(table)
        si_doc.add_page_break()

        # with main.add_figure() as figure:
        #     figure.caption = f'a) ASM and b) EDA energy terms along the C=X stretching of the reaction of {formula.molecule("H2C=X + CH3•", "html")} (X={formula.molecule("CH2", "html")}, NH, O) via the <b>C</b>-addition pathway. Transition states are respresented as dots. The consistent C=X distance is shown as the vertical grey line.'
        #     figure.add_image('../figs/ASM_CNO.png', 0, 0, label='a)')
        #     figure.add_image('../figs/EDA_CNO.png', 0, 1, label='b)')
        # main.add_page_break()

        # with si_doc.add_figure() as figure:
        #     figure.caption = f"Activation strain model (top row) and energy decomposition analysis (bottom row) energy terms along the C=X stretching of the reaction of {formula.molecule('H2C=X + CH3•', 'html')} (X={formula.molecule('CH2', 'html')}, NH, O) via the <b>C</b>-addition pathway. The consistent C=X stretch (0.0235 Å) is shown as the vertical grey line."
        #     figure.add_image("../figs/Multiplot_CNO_0.png", 0, 0)
        #     figure.add_image("../figs/Multiplot_CNO_1.png", 0, 1)
        #     figure.add_image("../figs/Multiplot_CNO_2.png", 0, 2)
        #     figure.add_image("../figs/Multiplot_CNO_3.png", 1, 0)
        #     figure.add_image("../figs/Multiplot_CNO_4.png", 1, 1)
        #     figure.add_image("../figs/Multiplot_CNO_5.png", 1, 2)
        # si_doc.add_page_break()


if __name__ == "__main__":
    write_xyz_SI()
    write_table_SI()
