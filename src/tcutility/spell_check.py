import numpy as np
from tcutility import log


def naive_recursive(a: str, b: str) -> float:
    '''
    The naïve recursive algorithm to obtain the Levenshtein distance between two strings.
    We do not recommend using this algorithm as it is quite slow and faster alternatives exist.

    Args:
        a, b: strings to compare.

    Returns:
        The Levenshtein distance between the strings ``a`` and ``b``.

    .. seealso::
        :func:`wagner_fischer`
            A more efficient algorithm to obtain the Levenshtein distance (up to 25x faster).
    '''
    if len(b) == 0:
        return len(a)
    if len(a) == 0:
        return len(b)

    def tail(s):
        return s[1:]

    if a[0] == b[0]:
        return naive_recursive(tail(a), tail(b))

    d = 1 + min(naive_recursive(tail(a), b), naive_recursive(a, tail(b)), naive_recursive(tail(a), tail(b)))
    return d


def wagner_fischer(a: str, b: str, substitution_cost: float = 1, case_missmatch_cost: float = 1, insertion_cost: float = 1) -> float:
    '''
    Return the Levenshtein distance using the Wagner-Fischer algorithm.
    You can also change the penalty for various errors for this algorithm.
    By default, all types of errors incur a penalty of 1.

    Args:
        a, b: strings to compare.
        substitution_cost: the penalty for the erroneous substitution of a character.
        case_missmatch_cost: the penalty for miss-matching the case of a character.
        insertion_cost: the cost for the erroneous insertion or deletion of a character.
    
    Returns:
        The Levenshtein distance between the strings ``a`` and ``b``.

    Example:
        .. code-block:: python

            >>> wagner_fischer('kitten', 'sitting')
            3

    .. seealso::
        :func:`naive_recursive`
            An alternative (and slower) algorithm to obtain the Levenshtein distance.
    '''
    # initialize an empty matrix
    d = np.zeros((len(a)+1, len(b)+1)).astype(float)

    # the top row and left column are always the same
    for i in range(len(a)):
        d[i+1, 0] = i+1
    for i in range(len(b)):
        d[0, i+1] = i+1

    # iteratively build the matrix
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            # if the two characters are the same the cost is 0
            if a[i-1] == b[j-1]:
                cost = 0
            # case miss-match
            elif a[i-1].lower() == b[j-1].lower():
                cost = case_missmatch_cost
            # substitution
            else:
                cost = substitution_cost

            # here determine if the substitution/miss-match cost is greater than the insertion or deletion cost
            d[i, j] = min(d[i-1, j] + insertion_cost, d[i, j-1] + insertion_cost, d[i-1, j-1] + cost)

    # return the bottom-right element, this is the final edit-distance
    return d[-1, -1]


def get_closest(a: str, others: list[str], compare_func=wagner_fischer, ignore_case: bool = False, ignore_chars: str = '', maximum_distance: int = None) -> list[str]:
    '''
    Return strings that are similar to an input string using the Levenshtein distance.

    Args:
        a: the string to compare the rest to.
        others: a collection of strings to compare to a. The returned strings will be taken from this collection.
        compare_func: the function to use to compare the strings. Defaults to the efficient :func:`wagner_fischer` algorithm.
        ignore_case: whether the case of the strings is taken into account. If enabled, all strings are turned to lower-case before comparison.
        ignore_chars: a strings specifying characters that should be ignored.
        maximum_distance: the maximum Levenshtein distance to allow. 
            If it is lower than the lowest distance for the collection of strings, we return the strings with the lowest distance. 
            If set to ``None`` we return the lowest distance strings.

    Returns:
        A collection of strings that have a Levenshtein distance to ``a`` below ``maximum_distance`` 
        or have the lowest distance to ``a`` if all strings have a distance greater than ``maximum_distance``.

    Example:
        .. code-block:: python

            >>> closest = get_closest('kitten', ['mitten', 'bitten', 'sitting'])
            >>> print(closest)
            ['mitten', 'bitten']
    '''
    if ignore_case:
        a = a.lower()

    for char in ignore_chars:
        a = a.replace(char, '')

    dists = []
    for other in others:
        if ignore_case:
            other = other.lower()

        for char in ignore_chars:
            other = other.replace(char, '')

        dists.append(compare_func(a, other))

    if maximum_distance is None:
        maximum_distance = -1
    lowest_strs = [other for dist, other in zip(dists, others) if dist <= max(maximum_distance, min(dists))]
    return lowest_strs


def make_suggestion(a: str, others: list[str], **kwargs):
    '''
    Print a warning that gives suggestions for strings that are close to a given string.

    Example:
        .. code-block:: python

            >>> make_suggestion('kitten', ['mitten', 'bitten', 'sitting'])
            [2024/01/30 15:26:35] [WARNING](main): Could not find "kitten". Did you mean mitten or bitten?

    .. seealso::
        :func:`get_closest` for a description of the function arguments.
    '''
    closest = get_closest(a, others, **kwargs)

    if len(closest) > 1:
        closest_string = " or ".join([", ".join(closest[:-1]), closest[-1]])
    else:
        closest_string = closest[0]

    # write a warning message
    log.warn(f'Could not find "{a}". Did you mean {closest_string}?', caller_level=3)
