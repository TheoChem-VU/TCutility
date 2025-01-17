import click
from tcutility.cli_scripts.cite import generate_citations
from tcutility.cli_scripts.concatenate_irc import concatenate_irc_paths
from tcutility.cli_scripts.geo import calculate_geometry_parameter
from tcutility.cli_scripts.job_script import optimize_geometry
from tcutility.cli_scripts.read import read_results
from tcutility.cli_scripts.resize_figures import resize



@click.group()
def tc():
    """TCutility command line interface."""
    pass


tc.add_command(read_results, name="read")
tc.add_command(optimize_geometry, name="optimize")
tc.add_command(generate_citations, name="cite")
tc.add_command(calculate_geometry_parameter, name="geo")
tc.add_command(concatenate_irc_paths, name="concat-irc")
tc.add_command(resize, name="resize")

if __name__ == "__main__":
    tc()
