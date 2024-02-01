tcutility.job
===================================

Overview
--------

This module offers you the tools to efficiently and easily build computational workflows with various engines. 
The module defines usefull classes that do all the heavy lifting (input and runscript preparation) in the background, while ensuring correctness of the generated inputs

Job classes
***********

Jobs are run using subclasses of the |Job| class. The base |Job| class handles setting up directories and running the calculations. 

The |Job| subclasses are also context-managers, which results in cleaner and more error-proof code:

.. code-block:: python
   :linenos:

   from tcutility.job import ADFJob

   # job classes are also context-managers
   # when exiting the context-manager the job will automatically be run
   # this ensures you won't forget to start the job
   with ADFJob() as job:
       job.molecule('example.xyz')

   # you can also not use the context-manager
   # in that case, don't forget to run the job
   job = ADFJob()
   job.molecule('example.xyz')
   job.run()

You can control where a calculation is run by changing the ``job.name`` and ``job.rundir`` properties.

.. code-block:: python
   :linenos:

   from tcutility.job import ADFJob

   with ADFJob() as job:
       job.molecule('example.xyz')
       job.rundir = './calc_dir/molecule_1'
       job.name = 'ADF_calculation'

   print(job.workdir)

This script will run a single point calculation using ADF in the working directory ``./calc_dir/molecule_1/ADF_calculation``. You can access the full path to the working directory using the ``job.workdir`` property.


Slurm support
*************

One usefull feature is that the |Job| class detects if slurm is able to be used on the platform the script is running on. If slurm is available, jobs will be submitted using ``sbatch`` instead of ran locally. It is possible to set any ``sbatch`` option you would like.

.. code-block:: python
   :linenos:

   from tcutility.job import ADFJob

   with ADFJob() as job:
       job.molecule('example.xyz')
       # we can set any sbatch settings using the job.sbatch() method
       # in this case, we set the partition to 'tc' and the number of cores to 32
       job.sbatch(p='tc', n=32)

Job dependencies
****************

It is possible to setup dependencies between jobs. This allows you to use the results of one calculation as input for a different calculation.

.. code-block:: python
    :linenos:

    from tcutility.job import ADFJob, CRESTJob

    # submit and run a CREST calculation
    with CRESTJob() as crest_job:
        crest_job.molecule('input.xyz')
        crest_job.sbatch(p='tc', n=32)

        crest_job.rundir = './calculations/molecule_1'
        crest_job.name = 'CREST'

    # get the 10 lowest conformers using the crest_job.get_conformer_xyz() method
    for i, conformer_xyz in enumerate(crest_job.get_conformer_xyz(10)):
        # set up the ADF calculation
        with ADFJob() as opt_job:
            # make the ADFJob depend on the CRESTJob
            # slurm will wait for the CRESTJob to finish before starting the ADFJob
            opt_job.dependency(crest_job)
            # you can set a file to an xyz-file 
            # that does not exist yet as the molecule
            opt_job.molecule(conformer_xyz)
            opt_job.sbatch(p='tc', n=16)

            opt_job.functional('OLYP-D3(BJ)')
            opt_job.basis_set('TZ2P')
            opt_job.quality('Good')
            opt_job.optimization()

            opt_job.rundir = './calculations/molecule_1'
            opt_job.name = f'conformer_{i}'

This script will first setup and submit a |CRESTJob| calculation to generate conformers for the structure in ``input.xyz``. It will then submit geometry optimizations for the 10 lowest conformers using |ADFJob| at the ``OLYP-D3(BJ)/TZ2P`` level of theory. Slurm will first wait for the |CRESTJob| calculation to finish before starting the |ADFJob| calculations.

Supported engines
*****************

We currently support the following engines and job classes:

* `Amsterdam Density Functional (ADF) <https://www.scm.com/product/adf/>`_

  * |ADFJob|, regular ADF calculations
  * |ADFFragmentJob|, fragment based calculations
  * |NMRJob|, Nuclear Magnetic Resonance (NMR) calculations using ADF


* `Density Functional with Tight Binding (DFTB) <https://www.scm.com/product/dftb/>`_

  * |DFTBJob|, regular DFTB calculations

* `ORCA <https://www.faccts.de/orca/>`_

  * |ORCAJob|, regular ORCA calculations

* `Conformer rotamer ensemble sampling tool (CREST) <https://github.com/crest-lab/crest>`_ including `Quantum Cluster Growth (QCG)  <https://crest-lab.github.io/crest-docs/page/overview/workflows.html#quantum-cluster-growth-qcg>`_

  * |CRESTJob|, CREST conformational search
  * |QCGJob|, QCG explicit solvation search

See the `API Documentation <./api/tcutility.job.html>`_ for an overview of the Job classes offered by tcutility.job module.

.. note::
	
	If you want support for new engines/classes, please open an issue on our GitHub page, or let one of the developers know!

Requirements
------------

To run calculations related to the Amsterdam Modelling Suite (AMS) you will require a license.

For ORCA calculations you will need to add the ORCA executable to your PATH.


Examples
--------
A few typical use-cases are given below. Click `here <./examples.html>`_ for a full overview of all examples.

Geometry optimization using ADF
*******************************

It is quite easy to set up calculations using the :mod:`tcutility.job` package. 
For example, if we want to run a simple geometry optimization using ADF we can use the |ADFJob| class.

In this case we are optimizing the water dimer at the ``BP86-D3(BJ)/TZ2P`` level.
To handle the ADF settings you can refer to the GUI. For example, to use a specific functional simply enter the name of the functional as it appears in the ADF GUI. The same applies to pretty much all settings. The |ADFJob| class will handle everything in the background for you.

The job will be run in the ``./calculations/GO_water_dimer`` directory. The :mod:`tcutility.job` package will handle running of the calculation as well. It will detect if your platform supports slurm and if it does, will use ``sbatch`` to run your calculations. Otherwise, it will simply run the calculation locally.

.. tabs::

	.. group-tab:: Runscript (:download:`󠀠download <../examples/job/GO_water_dimer.py>`)

		.. literalinclude:: ../examples/job/GO_water_dimer.py
		   :language: python
		   :linenos:

	.. group-tab:: XYZ-file (:download:`󠀠download <../examples/job/water_dimer.xyz>`)

		.. literalinclude:: ../examples/job/water_dimer.xyz

Fragment calculation using ADF
******************************

Another common usage of ADF is running a fragment calculation. This calculation requires setting up three different ADF jobs. Using the :mod:`tcutility.job` package allows you to set up and run these kinds of calculations in as little as 8 lines of code.

In this case we make use of a special xyz file format (see :func:`tcutility.molecule.guess_fragments`) which specifies the fragments. This saves us some work in setting up the calculations.

.. tabs::

	.. group-tab:: Runscript (:download:`󠀠download <../examples/job/frag_NH3BH3.py>`)

		.. literalinclude:: ../examples/job/frag_NH3BH3.py
		   :language: python
		   :linenos:

	.. group-tab:: XYZ-file (:download:`󠀠download <../examples/job/NH3BH3.xyz>`)

		.. literalinclude:: ../examples/job/NH3BH3.xyz
