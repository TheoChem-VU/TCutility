from time import perf_counter
import numpy as np
from tcutility import log
from types import FunctionType
import listfunc
import atexit
'''
Implements a decorator and context manager that records and stores the number of times a function
has been called and also the amount of time taken in total/per call
'''
times = {}
exec_start = perf_counter()

enabled: bool = True


class timer:
    '''
    The main timer class. It acts both as a context-manager and decorator.
    '''
    def __init__(self, name=None):
        if isinstance(name, FunctionType):
            self.function = name
            times.setdefault(name.__qualname__, {'calls': 0, 'timings': []})
        else:
            self.name = name
            times.setdefault(self.name, {'calls': 0, 'timings': []})

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *args, **kwargs):
        times[self.name]['calls'] += 1
        times[self.name]['timings'].append(perf_counter() - self.start)

    def __call__(self, *args, **kwargs):
        times.setdefault(self.function.__qualname__, {'calls': 0, 'timings': []})

        if enabled and __debug__:
            start = perf_counter()
            ret = self.function(*args, **kwargs)
            times[self.function.__qualname__]['calls'] += 1
            times[self.function.__qualname__]['timings'].append(perf_counter() - start)
            return ret
        else:
            return self.function(*args, **kwargs)


def print_timings():
    if not enabled:
        return

    names = list(times.keys())
    names = sorted(names)
    names_splits = [name.split('.') for name in names]

    # generate names that are common to multiple names
    for i, name in enumerate(names_splits):
        parents = []
        for name_ in names_splits[:i][::-1]:
            parents.append(".".join(listfunc.common_list(name, name_)))

        parents = [parent for parent in parents if parent]
        if parents != []:
            longest_parent = sorted(parents, key=lambda x: len(x))[-1]
            if longest_parent not in names:
                names.append(longest_parent)

    names = sorted(names)
    names_splits = [name.split('.') for name in names]
    # get the parents:
    parents = []
    parent_levels = []
    for i, (name, splits) in enumerate(zip(names, names_splits)):
        parent = 'TOTAL'
        parent_level = 0
        for name_, splits_ in zip(names[:i], names_splits[:i]):
            if listfunc.startswith(splits, splits_):
                parent = name_
                parent_level += 1
        parents.append(parent)
        parent_levels.append(parent_level)

    parent_times = {parent: {'timings': [sum([sum(times.get(name, {'timings': [0]})['timings']) for name in names if name.startswith(parent)])]} for parent in parents}
    for parent in parents:
        if parent in times:
            parent_times[parent] = {'timings': times[parent]['timings'], 'calls': times[parent]['calls']}
    parent_times['TOTAL'] = {'timings': [perf_counter() - exec_start], 'calls': 1}

    header = ['Function', 'Calls', 'Mean (s)', 'Time Spent (s)', 'Rel. Time']
    times_ = parent_times.copy()
    times_.update(times)
    lines = []
    for name, parent, level in zip(names, parents, parent_levels):
        line = []
        line.append(name.replace(parent, ' > ' * level))  # function name
        mean = np.mean(times_[name]["timings"])
        total = np.sum(times_[name]["timings"])
        calls = times_[name].get("calls", 0)
        if calls == 0:
            line.append('')
            line.append('')
        else:
            line.append(str(calls))
            line.append(f'{mean:.3f}')

        line.append(f'{total:.3f}')
        try:
            rel = sum(times_[name]["timings"])/sum(parent_times[parent]["timings"])*100
            rel_total = sum(times_[name]["timings"])/sum(parent_times["TOTAL"]["timings"])*100
        except ZeroDivisionError:
            rel = 0
            rel_total = 0
        if parent != 'TOTAL':
            line.append(f'{rel_total: >3.0f}% ({rel: >3.0f}%)')
        else:
            line.append(f'{rel_total: >3.0f}%')

        lines.append(line)
    lines.append(['TOTAL', '', '', f'{sum(times_["TOTAL"]["timings"]):.3f}', '100%'])
    
    log.table(lines, header=header, hline=[-2])


# this makes sure that the timings are printed when Python quits running
atexit.register(print_timings)
