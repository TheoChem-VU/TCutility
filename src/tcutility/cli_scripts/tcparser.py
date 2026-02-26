import click
from tcutility.cli_scripts.cite import generate_citations
from tcutility.cli_scripts.concatenate_irc import concatenate_irc_paths
from tcutility.cli_scripts.geo import calculate_geometry_parameter
from tcutility.cli_scripts.job_script import optimize_geometry
from tcutility.cli_scripts.read import read_results
from tcutility.cli_scripts.resize_figures import resize
from tcutility.cli_scripts.workflow import workflow


@click.group()
def tcutility():
    """TCutility command line interface."""
    pass


tcutility.add_command(read_results)
tcutility.add_command(optimize_geometry)
tcutility.add_command(generate_citations)
tcutility.add_command(calculate_geometry_parameter)
tcutility.add_command(concatenate_irc_paths)
tcutility.add_command(resize)
tcutility.add_command(workflow)
