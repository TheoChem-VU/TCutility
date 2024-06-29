import pathlib as pl
from typing import Dict, List

import tcutility.results as results

calc_outfile_map: Dict[str, pl.Path] = {
    "adf_geo_multikeys.txt": pl.Path() / "test" / "fixtures" / "ethanol",
    "adf_ts_multikeys.txt": pl.Path() / "test" / "fixtures" / "2",
    "dft_geo_multikeys.txt": pl.Path() / "test" / "fixtures" / "ethane",
    "orca_geo_multikeys.txt": pl.Path() / "test" / "fixtures" / "orca" / "optimization",
    "orca_freq_multikeys.txt": pl.Path() / "test" / "fixtures" / "orca" / "sp_freq",
}


def _get_multikeys(path_to_adf_calc_folder: pl.Path) -> List[str]:
    info = results.read(path_to_adf_calc_folder)
    multi_keys = info.multi_keys()
    return multi_keys


def _format_multikeys(multi_keys: List[str]) -> str:
    return "\n".join(multi_keys)


def main():
    current_dir = pl.Path(__file__).parent.resolve()
    output_doc_folder = current_dir.parent / "_static" / "result"

    for output_file_name, calc_dir in calc_outfile_map.items():
        multi_keys = _get_multikeys(calc_dir)
        formatted_multikeys = _format_multikeys(multi_keys)
        output_file = output_doc_folder / output_file_name
        output_file.write_text(formatted_multikeys)


if __name__ == "__main__":
    main()
