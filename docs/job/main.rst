TCutility.job module
====================

This module offers you the tools to efficiently and easily build computational workflows with various engines. 
The module defines usefull classes that do all the heavy lifting (input and runscript preparation) in the background.


We currently support the following engines:

* `ADF <https://www.scm.com/product/adf/>`_
* `DFTB <https://www.scm.com/product/dftb/>`_
.. * `BAND <https://www.scm.com/product/band_periodicdft/>`_
* `ORCA <https://www.faccts.de/orca/>`_
* `CREST <https://github.com/crest-lab/crest>`_
* `Quantum Cluster Growth (QCG)  <https://crest-lab.github.io/crest-docs/page/overview/workflows.html#quantum-cluster-growth-qcg>`_

See the API documentation for an overview of the Job classes offered by TCutility.job module.

Requirements
============

To run calculations related to the Amsterdam Modelling Suite (AMS) you will require a license.

For ORCA calculations you will need to add the ORCA executable to your PATH.


Example
=======

For example, running a fragment calculation using ADF requires setting up three different ADF jobs. Using the TCutility.job module allows you to set up these kinds of jobs in as little as 8 lines of code.

.. tabs::

	.. group-tab:: run.py

		.. code-block:: python

			from tcutility.job import ADFFragmentJob
			from tcutility import molecule

			mol = molecule.load('NH3BH3.xyz')

			fragment_indices = {flag.removeprefix('frag_'): x for flag, x in mol.flags.items() if flag.startswith('frag_')}

			with ADFFragmentJob() as job:
				job.molecule(mol)
				for fragment_name, indices in fragment_indices.items():
					job.add_fragment(indices, fragment_name)


	.. group-tab:: NH3BH3.xyz

		.. code-block::

			8

			N       0.00000000       0.00000000      -0.81474153
			B      -0.00000000      -0.00000000       0.83567034
			H       0.47608351      -0.82460084      -1.14410295
			H       0.47608351       0.82460084      -1.14410295
			H      -0.95216703       0.00000000      -1.14410295
			H      -0.58149793       1.00718395       1.13712667
			H      -0.58149793      -1.00718395       1.13712667
			H       1.16299585      -0.00000000       1.13712667

			frag_Donor = 1, 3, 4, 5
			frag_Acceptor = 2, 6, 7, 8

