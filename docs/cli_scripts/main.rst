Command-line interface (CLI) scripts
====================================

TCutility comes with some helpful CLI scripts for you to use. Please find an overview and examples here. You can also access information by using the ``tc -h`` command. This will show you an overview of the available CLI scripts. More detailed descriptions can be accessed using the ``tc {program name} -h`` commands.

Overview
--------

CLI scripts are invoked using the parent ``tc`` command followed by the sub-program (see below). If you have suggestions for useful scripts please contact the developers or `open an issue <https://github.com/TheoChem-VU/TCutility/issues/new>`_ on our GitHub page.

.. argparse::
    :filename: ../src/tcutility/cli_scripts/tcparser.py
    :func: create_parser
    :prog: tc

