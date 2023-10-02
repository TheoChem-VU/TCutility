ensure_list = lambda x: [x] if not isinstance(x, (list, tuple, set)) else x  # noqa: E731
squeeze_list = lambda x: x[0] if len(x) == 1 else x  # noqa: E731

from TCutility import analysis, results, constants  # noqa: F401, E402
