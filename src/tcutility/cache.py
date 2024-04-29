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
    '''
    Retrieve results from a JSON file.
    '''
    # open the file and parse the data
    with open(file) as cfile:
        data = json.loads(cfile.read())

    # we now go through the data
    # it is formatted as a list of dicts
    # each dict has the 'func', 'args', 'kwargs' and 'value' keys
    for datum in data:
        # func is set as the function qualname
        if datum['func'] != func.__qualname__:
            continue

        # args is retrieved as a list
        if datum['args'] != list(args):
            continue

        # kwargs is simply a dict
        if datum['kwargs'] != kwargs:
            continue

        # if we did not exit the loop yet we return the value
        return datum['value']


def _write_to_cache_file(file, func, args, kwargs, value):
    '''
    Write results to the file.
    '''
    # we open the file to get the data
    with open(file) as cfile:
        data = json.loads(cfile.read())

    # add the new results to the file
    new = {
        'func': func.__qualname__,
        'args': args,
        'kwargs': kwargs,
        'value': value
    }
    data.append(new)

    with open(file, 'w+') as cfile:
        cfile.write(json.dumps(data, indent=4))


def _clear_cache_file(file):
    '''
    Function that clears a file and writes a new beginning of a list.
    '''
    with open(file, 'w+') as cfile:
        cfile.write('[]')


def cache_file(file):
    '''
    Function decorator that stores results of a function to a file.

    Args:
        file: the filepath to store function call results to.
    '''
    def decorator(func):
        # make the file if it doesnt exist
        if not os.path.exists(file):
            _clear_cache_file(file)

        @functools.wraps(func)
        def inner_decorator(*args, **kwargs):
            # check if the arguments were called before
            cached = _get_from_cache_file(file, func,  args, kwargs)
            if cached is not None:
                return cached

            # if it is not present we add it to the cache file
            res = func(*args, **kwargs)
            _write_to_cache_file(file, func,  args, kwargs, res)
            return res

        return inner_decorator
    return decorator




# if __name__ == '__main__':
    @cache_file('test.json')
    def test(a, b, c):
        return a + b * c

    test(1, 2, 3)
    test(1, 2, 3)
    test(1, 4, 3)
    test(1, 2, 3)
    test(1, 4, 3)
