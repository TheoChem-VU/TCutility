import os
import re
from typing import Dict, List
import glob

from tcutility import results

j = os.path.join


def split_all(path: str) -> List[str]:
    """
    Split a path into all of its parts.

    Args:
        path: the path to be split, it will be separated using :func:`os.path.split`.

    Returns:
        A list of parts of the original path.

    Example:
        .. code-block:: python

            >>> split_all('a/b/c/d')
            ['a', 'b', 'c', 'd']
    """
    path = os.path.normpath(path)
    parts = []
    while True:
        a, b = os.path.split(path)
        if not a or not b:
            parts.append(path)
            return parts[::-1]
        parts.append(b)
        path = a


def get_subdirectories(root: str, include_intermediates: bool = False, max_depth: int = None, _current_depth: int = 0) -> List[str]:
    """
    Get all sub-directories of a root directory.

    Args:
        root: the root directory.
        include_intermediates: whether to include intermediate sub-directories instead of only the lowest levels.
        max_depth: the maximum depth depth to look for subdirectories, 
            e.g. setting it to `1` will return only the contents of the `root` path.

    Returns:
        A list of sub-directories with ``root`` included in the paths.

    Example:
        Given a file-structure as follows:

        .. code-block::

            root
            |- subdir_a
            |  |- subsubdir_b
            |  |- subsubdir_c
            |- subdir_b
            |- subdir_c

        Then we get the following outputs.

        .. tabs::

            .. group-tab:: Including intermediates

                .. code-block:: python

                    >>> get_subdirectories('root', include_intermediates=True)
                    ['root',
                     'root/subdir_a',
                     'root/subdir_a/subsubdir_b',
                     'root/subdir_a/subsubdir_c',
                     'root/subdir_b',
                     'root/subdir_c']

            .. group-tab:: Excluding intermediates

                .. code-block:: python

                    >>> get_subdirectories('root', include_intermediates=False)
                    ['root/subdir_a/subsubdir_b',
                     'root/subdir_a/subsubdir_c',
                     'root/subdir_b',
                     'root/subdir_c']
    """
    contents = []
    if _current_depth == 0 and include_intermediates:
        contents.append(root)

    with os.scandir(root) as scanner:
        for entry in scanner:
            if entry.is_file():
                continue

            if _current_depth == max_depth:
                contents.append(entry.path)
                continue

            sub_contents = list(get_subdirectories(entry.path, include_intermediates=include_intermediates, _current_depth=_current_depth+1, max_depth=max_depth))

            if include_intermediates or len(sub_contents) == 0:
                contents.append(entry.path)

            contents.extend(sub_contents)

    return contents


def path_depth(path: str) -> int:
    """
    Calculate the depth of a given path.
    """
    return len(split_all(path))


def match(root: str, pattern: str, sort_by: str = None) -> Dict[str, dict]:
    """
    Find and return information about subdirectories of a root that match a given pattern.

    Args:
        root: the root of the subdirectories to look in.
        pattern: a string specifying the pattern the subdirectories should correspond to.
            It should look similar to a format string, without the ``f`` in front of the string.
            Inside curly braces you can put a variable name, which you can later extract from the results.
            Anything inside curly braces will be matched to word characters (``[a-zA-Z0-9_-]``) including dashes and underscores.
        sort_by: the key to sort the results by. If not given, the results will be returned in the order they were found.

    Returns:
        A |Result| object containing the matched directories as keys and information (also |Result| object) about those matches as the values. Each information dictionary contains the variables given in the pattern.
        E.g. using a pattern such as ``{a}/{b}/{c}`` will populate the ``info.a``, ``info.b`` and ``info.c`` keys of the info |Result| object.

    Example:
        Given a file-structure as follows:

        .. code-block::

            root
            |- NH3-BH3
            |   |- BLYP_QZ4P
            |   |  |- extra_dir
            |   |  |- blablabla
            |   |
            |   |- BLYP_TZ2P
            |   |  |- another_dir
            |   |
            |   |- M06-2X_TZ2P
            |
            |- SN2
            |   |- BLYP_TZ2P
            |   |- M06-2X_TZ2P
            |   |  |- M06-2X_TZ2P

        We can run the following scripts to match the subdirectories.

        .. code-block:: python

            from tcutility import log
            # get the matches, we want to extract the system name (NH3-BH3 or SN2)
            # and the functional and basis-set
            # we don't want the subdirectories
            matches = match('root', '{system}/{functional}_{basis_set}')

            # print the matches as a table
            rows = []
            for d, info in matches.items():
                rows.append([d, info.system, info.functional, info.basis_set])

            log.table(rows, ['Directory', 'System', 'Functional', 'Basis-Set'])

        which prints

        .. code-block::

            [2024/01/17 14:39:08] Directory                  System    Functional   Basis-Set
            [2024/01/17 14:39:08] ───────────────────────────────────────────────────────────
            [2024/01/17 14:39:08] root/SN2/M06-2X_TZ2P       SN2       M06-2X       TZ2P
            [2024/01/17 14:39:08] root/NH3-BH3/BLYP_TZ2P     NH3-BH3   BLYP         TZ2P
            [2024/01/17 14:39:08] root/NH3-BH3/M06-2X_TZ2P   NH3-BH3   M06-2X       TZ2P
            [2024/01/17 14:39:08] root/SN2/BLYP_TZ2P         SN2       BLYP         TZ2P
            [2024/01/17 14:39:08] root/NH3-BH3/BLYP_QZ4P     NH3-BH3   BLYP         QZ4P
"""
    # get the number and names of substitutions in the given pattern
    substitutions = re.findall(r"{(\w+)}", pattern)
    # the pattern should resolve to words and may contain - and _

    # given the substitutions we build a regex pattern and a glob pattern
    glob_pattern = pattern
    for sub in substitutions:
        pattern = pattern.replace("{" + sub + "}", "([a-zA-Z0-9_.-]+)")
        glob_pattern = glob_pattern.replace("{" + sub + "}", "*")

    # get all applicable subdirectories
    subdirs = glob.glob(os.path.join(root, glob_pattern))

    # compile a regular expression pattern to match with later
    regex = re.compile(pattern)

    # go through all applicable subdirectories and retrieve the information we want
    ret = results.Result()
    for subdir in subdirs:
        # subdir = os.path.relpath(subdir, root)
        subdir = subdir[len(f'{root}/'):]
        p = j(root, subdir)
        re_match = regex.fullmatch(subdir)
        ret[p] = results.Result(**{substitutions[i]: re_match.group(i + 1) for i in range(len(substitutions))})

    if not sort_by:
        return ret

    # if requested we sort the results before returning them
    return results.Result(sorted(ret.items(), key=lambda d: d[1][sort_by]))
