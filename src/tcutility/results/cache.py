'''
Tiny module that handles caching rkf files. 
rkf files take a long time to open (especially {engine}.rkf), so it is better to open them once and cache them for later use
'''
from scm import plams
from typing import Union, Any

# the actual cache is stored in this dict
_cache = {}


class TrackKFReader(plams.KFReader):
    """Subclass of plams.KFReader that also tracks the variables that were read. This class can be useful to figure out which variables are important. 
    For example, we can then trim rkf files to reduce their filesizes."""
    def __init__(self, *args, **kwargs):
        self.tracker = []
        super().__init__(*args, **kwargs)

    def read(self, section: str, variable: str) -> Any:
        '''Read a variable from a section of an rkf file and store the accessed section and variable in the tracker.

        Args:
            section: Name of the section to read from.
            variable: Name of the variable inside the section.

        Returns:
            Any value returned will be automatically converted into the correct type. E.g. text-based data will be converted to a string, numbers to floats or integers, etc.'''
            
        self.tracker.append((section, variable))
        return super().read(section, variable)


def store(reader: plams.KFReader) -> None:
    '''Store an rkf reader in the cache. It can later be indexed by its path.

    Args:
        reader: An rkf file reader object.'''
    path = reader.path
    _cache[path] = reader


def get(path: str) -> plams.KFReader:
    '''Retrieve an rkf reader from storage using its path. If the file was not opened yet, open it first and then store and return the new object.

    Args:
        path: path to the rkf file location.

    Returns:
        An rkf file reader that can be used for reading data from a calculation.
    '''
    # if the path is already in the cache, simply return it
    if path and path in _cache:
        return _cache[path]
    # else we will load the rkf file and store it in the cache
    reader = TrackKFReader(path)
    store(reader)
    return reader


def unload(arg: Union[str, plams.KFReader]):
    '''Delete an rkf reader from storage. Since rkf files can be quite large, we should not forget to unload them after we have finished reading from them, lest we run into memory issues.

    Args:
        arg: Either a path pointing to the rkf file location or the reader itself.'''
    # if the arg is a key in the cache we will delete the key
    if arg in _cache:
        del _cache[arg]
        return
    # if it is not a key, find the key corresponding to the value and delete it
    if arg in _cache.values():
        key = [key for key, val in _cache.items() if val == arg][0]
        del _cache[key]
        return
