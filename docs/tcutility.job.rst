tcutility.job package
=====================

Overview
--------

This module offers you the tools to efficiently and easily build computational workflows with various engines. 
The module defines usefull classes that do all the heavy lifting (input and runscript preparation) in the background.


We currently support the following engines:

* `ADF <https://www.scm.com/product/adf/>`_
* `DFTB <https://www.scm.com/product/dftb/>`_
* `ORCA <https://www.faccts.de/orca/>`_
* `CREST <https://github.com/crest-lab/crest>`_
* `Quantum Cluster Growth (QCG)  <https://crest-lab.github.io/crest-docs/page/overview/workflows.html#quantum-cluster-growth-qcg>`_

See the `API Documentation <./api/tcutility.job.html>`_ for an overview of the Job classes offered by tcutility.job module.

Requirements
------------

To run calculations related to the Amsterdam Modelling Suite (AMS) you will require a license.

For ORCA calculations you will need to add the ORCA executable to your PATH.


Examples
--------


Geometry optimization using ADF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is quite easy to set up calculations using the :mod:`tcutility.job` package. 
For example, if we want to run a simple geometry optimization using ADF we can use the :class:`ADFJob <tcutility.job.adf.ADFJob>` class.

In this case we are optimizing the water dimer at the BP86-D3(BJ)/TZ2P level.
To handle the ADF settings you can refer to the GUI. For example, to use a specific functional simply enter the name of the functional as it appears in the ADF GUI. The same applies to pretty much all settings. The :class:`ADFJob <tcutility.job.adf.ADFJob>` class will handle everything in the background for you.

The job will be run in the ``./calculations/GO_water_dimer`` directory. The :mod:`tcutility.job` package will handle running of the calculation as well. It will detect if your platform supports slurm. If it does, it will use ``sbatch`` to run your calculations. Otherwise, it will simply run the calculation locally.

.. tabs::

	.. group-tab:: Runscript (:download:`󠀠download <../examples/job/GO_water_dimer.py>`)

		.. literalinclude:: ../examples/job/GO_water_dimer.py
		   :language: python
		   :linenos:

	.. group-tab:: XYZ-file (:download:`󠀠download <../examples/job/water_dimer.xyz>`)

		.. literalinclude:: ../examples/job/water_dimer.xyz

Fragment calculation using ADF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Another common usage of ADF is running a fragment calculation. This calculation requires setting up three different ADF jobs. Using the :mod:`tcutility.job` package allows you to set up these kinds of jobs in as little as 8 lines of code.

In this case we make use of a special xyz file format (see :func:`tcutility.molecule.guess_fragments`) which specifies the fragments. This saves us some work in setting up the calculations.

.. tabs::

	.. group-tab:: Runscript (:download:`󠀠download <../examples/job/frag_NH3BH3.py>`)

		.. literalinclude:: ../examples/job/frag_NH3BH3.py
		   :language: python
		   :linenos:

	.. group-tab:: XYZ-file (:download:`󠀠download <../examples/job/NH3BH3.xyz>`)

		.. literalinclude:: ../examples/job/NH3BH3.xyz
