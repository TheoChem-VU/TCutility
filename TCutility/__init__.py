ensure_list = lambda x: [x] if not isinstance(x, (list, tuple, set)) else x  # noqa: E731
squeeze_list = lambda x: x[0] if len(x) == 1 else x  # noqa: E731


def ensure_2d(x, transposed=False):
    x = ensure_list(x)
    if transposed:
        if not isinstance(x[0], (list, tuple, set)):
            x = [x]
    else:
        x = [ensure_list(y) for y in x]
    return x


from TCutility import analysis, results, constants, log, molecule  # noqa: F401, E402
