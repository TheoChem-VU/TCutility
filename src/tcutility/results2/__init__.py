from . import *  # noqa: F403
from . import result, detect_filetype

def read(path: str) -> result.NestedDict:  # noqa: F405
	program = detect_filetype.detect_program(path)  # noqa: F405
	if program == 'adf':
		return adf.read_adfrkf(path)  # noqa: F405
