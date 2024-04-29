import time
import functools
import json
import os


_timed_func_cache = {}
_time_since_cache = {}

_func_cache = {}

_general_cache = {}


def timed_cache(delay: float):
    '''
    Decorator that creates a timed cache for the function or method. 
    This cache will expire after a chosen amount of time.

    Args:
        delay: the expiry time for the function cache.
    '''
    def decorator(func):
        # this is the main decorator returned by timed_cache
        @functools.wraps(func)
        def inner_decorator(*args, **kwargs):
            # we have to create a tuple of the kwargs items to ensure we can hash the arguments
            arguments = args, tuple(kwargs.items())

            # the time since the last caching
            dT = time.perf_counter() - _time_since_cache[func]
            # if the cache has expired, we remove it from the cache
            # and set the new time_since_cache
            if dT >= delay:
                _timed_func_cache[func].pop(arguments, None)
                _time_since_cache[func] = time.perf_counter()

            # check if the arguments were called before
            if arguments in _timed_func_cache[func]:
                return _timed_func_cache[func][arguments]

            # if it is not present we add it to the cache
            res = func(*args, **kwargs)
            _timed_func_cache[func][arguments] = res
            return res

        # initialize the cache and time_since_cache
        _timed_func_cache[func] = {}
        _time_since_cache[func] = -delay

        return inner_decorator
    return decorator


def cache(func):
    '''
    Function decorator that stores results from previous calls to the function or method.
    '''
    @functools.wraps(func)
    def inner_decorator(*args, **kwargs):
        # we have to create a tuple of the kwargs items to ensure we can hash the arguments
        arguments = args, tuple(kwargs.items())

        # check if the arguments were called before
        if arguments in _func_cache[func]:
            return _func_cache[func][arguments]

        # if it is not present we add it to the cache
        res = func(*args, **kwargs)
        _func_cache[func][arguments] = res
        return res

    _func_cache[func] = {}
    return inner_decorator


def _get_from_cache_file(file, func, args, kwargs):
    with open(file) as cfile:
        data = json.loads(cfile.read())

    for datum in data:
        if datum['func'] != func.__qualname__:
            continue

        if datum['args'] != list(args):
            continue

        if datum['kwargs'] != kwargs:
            continue

        return datum['value']


def _write_to_cache_file(file, func, args, kwargs, value):
    with open(file) as cfile:
        data = json.loads(cfile.read())

    new = {
        'func': func.__qualname__,
        'args': args,
        'kwargs': kwargs,
        'value': value
    }
    data.append(new)

    # data.setdefault(func.__qualname__, {})
    # data[func.__qualname__][arguments] = value
    with open(file, 'w+') as cfile:
        cfile.write(json.dumps(data, indent=4))


def _clear_cache_file(file):
    with open(file, 'w+') as cfile:
        cfile.write('[]')


def cache_file(file):
    '''
    Function decorator that stores results of a function to a file.
    '''
    def decorator(func):
        # make the file if it doesnt exist
        if not os.path.exists(file):
            _clear_cache_file(file)

        @functools.wraps(func)
        def inner_decorator(*args, **kwargs):
            # we have to create a tuple of the kwargs items to ensure we can hash the arguments
            # arguments = args, list(kwargs.items())

            # check if the arguments were called before
            cached = _get_from_cache_file(file, func,  args, kwargs)
            if cached is not None:
                return cached

            # if it is not present we add it to the cache
            res = func(*args, **kwargs)
            _write_to_cache_file(file, func,  args, kwargs, res)
            return res

        return inner_decorator
    return decorator




# if __name__ == '__main__':
    # @timed_cache(1)
    # def test_timer(a, b):
    #     return a * b

    # _clear_cache_file('test.json')

    @cache_file('test.json')
    def test(a, b, c):
        return a + b * c

    test(1, 2, 3)
    test(1, 2, 3)
    test(1, 4, 3)
    test(1, 2, 3)
    test(1, 4, 3)

    # _write_to_cache_file('test.json', test, (1, 2, 3), {}, test(1, 2, 3))
