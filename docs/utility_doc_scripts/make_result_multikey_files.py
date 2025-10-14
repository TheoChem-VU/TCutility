import pathlib as pl
from enum import StrEnum

from tcutility.results.read import read


class OutputFileNames(StrEnum):
    ADF_CALC = "adf_multikeys.txt"


def _format_multikeys(multi_keys: list[str]) -> str:
    return "\n".join(multi_keys)


def main():
    current_dir = pl.Path(__file__).parent.resolve()
    output_doc_folder = current_dir.parent / "_static" / "result"
    path_to_adf_calc_folder = current_dir.parent.parent / "test" / "fixtures" / "ethanol"
    info = read(path_to_adf_calc_folder)

    multi_keys = info.multi_keys()

    for output_file_name in OutputFileNames:
        formatted_multikeys = _format_multikeys(multi_keys)
        output_file = output_doc_folder / output_file_name
        output_file.write_text(formatted_multikeys)


if __name__ == "__main__":
    main()
