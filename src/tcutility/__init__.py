# Job imports
from tcutility.cache import cache, cache_file, timed_cache
from tcutility import log
from tcutility.analysis.pyfrag import PyFragResult, get_pyfrag_results
from tcutility.analysis.task_specific.irc import concatenate_irc_trajectories
from tcutility.analysis.vdd.charge import VDDCharge

# from tcutility.analysis.vdd.manager import VDDChargeManager, create_vdd_charge_manager # Don't load in vdd as it has an annoying pandas dependency that cannot be avoided upon importing
from tcutility.analysis.vibration.ts_vibration import avg_relative_bond_length_delta, determine_ts_reactioncoordinate, validate_transitionstate
from tcutility.cite import cite, _get_doi_data, _get_doi_data_from_title, _get_doi_data_from_query, _get_publisher_city, _get_journal_abbreviation
from tcutility.connect import Connection, Local, Server, ServerFile
from tcutility.data.functionals import categories, functional_name_from_path_safe_name, functionals, get_available_functionals, get_functional
from tcutility.environment import requires_optional_package
from tcutility.geometry import KabschTransform, MolTransform, Transform, apply_rotmat, get_rotmat, rotate, rotmat_to_angles, vector_align_rotmat
from tcutility.job.adf import ADFFragmentJob, ADFJob
from tcutility.job.ams import AMSJob
from tcutility.job.crest import CRESTJob, QCGJob
from tcutility.job.dftb import DFTBJob
from tcutility.job.nmr import NMRJob
from tcutility.job.orca import ORCAJob
from tcutility.job.xtb import XTBJob
from tcutility.molecule import from_string, guess_fragments, load, number_of_electrons, save, write_mol_to_amv_file, write_mol_to_xyz_file
# from tcutility.report.report import SI
from tcutility.results.read import get_info, quick_status, read
from tcutility.results.result import Result
from tcutility.timer import timer

__all__ = [
    "ADFFragmentJob",
    "ADFJob",
    "AMSJob",
    "CRESTJob",
    "QCGJob",
    "DFTBJob",
    "NMRJob",
    "ORCAJob",
    "XTBJob",
    "log",
    "from_string",
    "guess_fragments",
    "load",
    "number_of_electrons",
    "save",
    "write_mol_to_amv_file",
    "write_mol_to_xyz_file",
    "get_info",
    "quick_status",
    "read",
    "Result",
    "timer",
    "Connection",
    "Local",
    "Server",
    "ServerFile",
    "cache",
    "cache_file",
    "cite",
    "requires_optional_package",
    "Transform",
    "KabschTransform",
    "MolTransform",
    "get_rotmat",
    "rotmat_to_angles",
    "apply_rotmat",
    "rotate",
    "vector_align_rotmat",
    "PyFragResult",
    "get_pyfrag_results",
    "concatenate_irc_trajectories",
    "VDDCharge",
    "avg_relative_bond_length_delta",
    "determine_ts_reactioncoordinate",
    "validate_transitionstate",
    "categories",
    "functionals",
    "functional_name_from_path_safe_name",
    "get_functional",
    "get_available_functionals",
    # "SI",
    "timed_cache",
]
