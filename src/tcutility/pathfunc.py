import os
import re
from typing import Dict, List

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
    parts = []
    while True:
        a, b = os.path.split(path)
        if not a or not b:
            parts.append(path)
            return parts[::-1]
        parts.append(b)
        path = a


def get_subdirectories(root: str, include_intermediates: bool = False) -> List[str]:
    """
    Get all sub-directories of a root directory.

    Args:
        root: the root directory.
        include_intermediates: whether to include intermediate sub-directories instead of only the lowest levels.

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
    dirs = [root]
    subdirs = set()

    while len(dirs) > 0:
        _dirs = []
        for cdir in dirs:
            csubdirs = [j(cdir, d) for d in os.listdir(cdir) if os.path.isdir(j(cdir, d))]
            if len(csubdirs) == 0:
                subdirs.add(cdir)
            else:
                if include_intermediates:
                    subdirs.add(cdir)
                _dirs.extend(csubdirs)

        dirs = _dirs

    return subdirs


def match(root: str, pattern: str, sort_by: str = None) -> Dict[str, dict]:
    """
    Find and return information about subdirectories of a root that match a given pattern.

    Args:
        root: the root of the subdirectories to look in.
        pattern: a string specifying the pattern the subdirectories should correspond to.
            It should look similar to a format string, without the ``f`` in front of the string.
            Inside curly braces you can put a variable name, which you can later extract from the results.
            Anything inside curly braces will be matched to word characters (``[a-zA-Z0-9_-]``) including dashes and underscores.

    Returns:
        | A |Result| object containing the matched directories as keys and information (also |Result| object) about those matches as the values.
        Each information dictionary contains the variables given in the pattern.
        | E.g. using a pattern such as ``{a}/{b}/{c}`` will populate the ``info.a``, ``info.b`` and ``info.c`` keys of the info |Result| object.

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
    substitutions = re.findall(r"{(\w+[+*?]?)}", pattern)
    # the pattern should resolve to words and may contain - and _
    # replace them here
    for sub in substitutions:
        quantifier = sub[-1] if sub[-1] in "+*?" else "+"
        pattern = pattern.replace("{" + sub + "}", f"([a-zA-Z0-9_-]{quantifier})")

    ret = results.Result()
    # root dir can be any level deep. We should count how many directories are in root
    root_length = len(split_all(root))
    # get all subdirectories first, we can loop through them later
    subdirs = get_subdirectories(root, include_intermediates=True)
    # remove the root from the subdirectories. We cannot use str.removeprefix because it was added in python 3.9
    subdirs = [j(*split_all(subdir)[root_length:]) for subdir in subdirs if len(split_all(subdir)[root_length:]) > 0]
    for subdir in subdirs:
        # check if we get a match with our pattern
        match = re.fullmatch(pattern, subdir)
        if not match:
            continue

        p = j(root, subdir)
        # get the group data and add it to the return dictionary. We skip the first group because it is the full directory path
        ret[p] = results.Result(directory=p, **{substitutions[i]: match.group(i + 1) for i in range(len(substitutions))})

    if not sort_by:
        return ret

    return results.Result(sorted(ret.items(), key=lambda d: d[1][sort_by]))


def path_depth(path: str) -> int:
    """
    Calculate the depth of a given path.
    """
    return len(split_all(path))

