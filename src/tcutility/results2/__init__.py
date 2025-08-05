from . import *  # noqa: F403


def read(path: str) -> result.NestedDict:
	program = detect_filetype.detect_program(path)  # noqa: F405
	if program == 'adf':
		return adf.read_adfrkf(path)  # noqa: F405
