

from . import result, detect_filetype, adf, adf_rkf


def read(path: str) -> result.NestedDict:
	program = detect_filetype.detect_program(path)
	if program == 'adf':
		return adf.read_adfrkf(path)
