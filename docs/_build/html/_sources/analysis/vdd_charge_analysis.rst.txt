VDD Charge Analysis module
===========================

When a calculation is performed and has succesfully finished, the VDD charge analysis module can be used to extract the Voronoi Deformation Density (`VDD <https://doi.org/10.1002/jcc.10351>`_) charges.
The VDD charges measure the charge flow between atoms (officially Voronoi cells) from non-interacting atoms ("promolecule") to atoms feeling the environment of other atoms (molecular enviroment).
If symmetry is used, the VDD charges can be decomposed into contributions of seperate irreducible representations.

Requirements
------------

* A finished calculation using the ADF engine.
* Location to the calculation directory with ams.rkf and adf.rkf files


Example
--------

First, relevant modules need to be loaded. These include pathlib for handling paths and tcutility.results for loading the results of the calculation.
In addition, the VDD manager module needs to be loaded which is the interface to performing VDD analyses.

.. note::

    For this example we use calculations found in the `VDD test directory`_ of the tcutility package.
    We assume that the you place the VDD test directory in the same directory as this script.
    See the `example python script <../../../../examples/vdd_analysis.py>`_ for a direct implementation

.. code-block:: python

    import pathlib as pl
    import tcutility.results as results
    from tcutility.analysis.vdd import manager

Now, the calculation directory needs to be specified and the calculation results can be loaded via the |read| function.
The next step is to create a |VDDmanager| object which is the interface to performing VDD analyses.


.. code-block:: python

    DIRS = {0: "fa_acid_amide_cs", 1: "fa_squaramide_se_cs", 2: "fa_donor_acceptor_nosym", 3: "geo_nosym"}

    # Specify the calculation directory
    base_dir = pl.Path(__file__).parent
    base_dir = base_dir / "VDD"
    calc_dir = base_dir / DIRS[1]

    calc_res = results.read(calc_dir)
    vdd_manager = manager.create_vdd_charge_manager(name=calc_dir.name, results=calc_res)

The |VDDmanager| object contains the total VDD charges, as well as the VDD charges for each irreducible representation.
To see the contents of the |VDDmanager|, simply print it. The charges are formatted as a table in the unit of milli electrons [me].
You can always change the unit of the charges by using the |change_unit| method.

.. code-block:: python

    vdd_manager.change_unit("me")  # Change the unit to electrons "e" (electrons) or "me" (milli electrons)

    # Print the VDD charges to standard output
    print(vdd_manager)

    # Output:
    fa_squaramide_se_cs
    VDD charges (in unit me):
    Frag   Atom   Total   AA     AAA
    1      1C     -40    -10    -30
    1     2Se    -165    -30   -134
    1      3C     -40    -10    -30
    1     4Se    -165    -30   -134
    1      5C     +26   +122    -96
    1      6C     +26   +122    -96
    2      7N     +62    -88   +150
    2      8H     +53     -2    +55
    2      9H     +63     +7    +56
    2     10N     +62    -88   +150
    2     11H     +63     +7    +56
    2     12H     +53     -2    +55

    Summed VDD charges (in unit me):
    Frag   Total   AA     AAA
    1     -357   +164   -521
    2     +357   -164   +521

See? It is that easy. The charges sum up to the total charge of the molecule (in this case 0). Also, the sum of irrep charges is equal to the total charge, as it should be.
It is possible to print the charges to both a text file (.txt) as well as a Excel (.xlsx) file. The Excel file is formatted as a table and can be used for further analysis.

.. code-block:: python

    output_dir = base_dir / "output"

    # Write the VDD charges to a text file (static method because multiple managers can be written to the same file)
    manager.VDDChargeManager.write_to_txt(output_dir, vdd_manager)

    # Write the VDD charges to an excel file
    vdd_manager.write_to_excel(output_dir)

To visualize the VDD charges further, the charge for each atom can be plotted in a bar graph using matplotlib. The plot is saved as a .png file.:

.. code-block:: python

    # Plot the VDD charges per atom in a bar graph
    vdd_manager.plot_vdd_charges_per_atom(output_dir)

.. image:: ../_static/analysis/VDD/VDD_charges_per_atom.png
    :align: center


Finally, multiple |VDDmanager| objects can be made and written to a single .txt file. This is useful when comparing multiple calculations.

.. code-block:: python

    # Multiple calculations can be combined into a single file
    calc_dirs = [base_dir / calc for calc in DIRS.values()]
    calc_res = [results.read(calc_dir) for calc_dir in calc_dirs]
    vdd_managers = [manager.create_vdd_charge_manager(name=calc_dir.name, results=res) for calc_dir, res in zip(calc_dirs, calc_res)]
    manager.VDDChargeManager.write_to_txt(output_dir, vdd_managers)

.. literalinclude:: ../_static/analysis/VDD/VDD_charges_per_atom.txt
    :language: python
    :lines: 1-


VDD analysis API
-----------------

Here is the implementation of the |VDDmanager| and |VDDcharge| classes. The central information contained in the |VDDmanager| is a dictionary containing the total charge, and irreps (if present) as keys and the a list of |VDDcharge| as value.
A |VDDcharge| does not only contain the charge itself, but also to which atom and frag index it belongs.


.. _VDD test directory: https://github.com/TheoChem-VU/TCutility/tree/VDD-charge-implementation-and-pathlib-rewrite/test/fixtures/VDD
