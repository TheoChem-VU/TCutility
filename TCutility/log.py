import sys
import os
from datetime import datetime
from time import perf_counter
import numpy as np
import json
from TCutility import ensure_2d
from typing import Any, Iterable, List

###########################################################
# MODULE LEVEL VARIABLES USED TO CHANGE LOGGING BEHAVIOUR #
logfile = sys.stdout  # stream or file to send prints to. Default sys.stdout is the standard Python print output
tab_level = 0  # number of tabs to add before a logged message. This is useful to build a sense of structure in a long output
max_width = 0  # maximum width of printed messages. Default 0 means unbounded
print_date = True  # print time stamp before a logged message
log_level = 20  # the level of verbosity. Messages with a log_level >= this number will be sent to logfile


class Emojis:
    '''
    Class containing some useful emojis and other characters.
    Supports dot-notation and indexation to get a character.

    E.g. Emojis.wait == Emojis['wait']
    '''
    wait = '🕒'
    good = '✅'
    cancel = '🛑'
    sleep = '💤'
    fail = '❌'
    send = '📤'
    receive = '📥'
    empty = '⠀⠀'
    finish = '🏁'
    warning = '⚠️'
    question = '❔'
    info = 'ℹ️'
    rarrow = '─>'
    larrow = '<─'
    lrarrow = rlarrow = '<─>'
    angstrom = 'Å' 

    def __init__(self):
        raise SyntaxError('Do not instantiate the Emojis-class.')

    def __class_getitem__(cls, item):
        return getattr(cls, item)


class NoPrint:
    '''
    Context-manager that suppresses printing. It works by redirecting prints to a temporary output file. 
    This file is deleted after exiting the context-manager.
    '''
    def __init__(self, stdout=None):
        self.stdout = stdout or logfile
        self.overflow = open(str(os.getpid()) + '_NOPRINT.tmp', 'w+')

    def __enter__(self):
        global logfile
        logfile = self.overflow

    def __exit__(self, *args, **kwargs):
        global logfile
        logfile = self.stdout
        self.overflow.close()
        os.remove(str(os.getpid()) + '_NOPRINT.tmp')


def time_stamp():
    '''
    Return the current timestamp in a "[YYYY/MM/DD HH:MM:SS] "" format.
    '''
    now = datetime.now()
    return f'[{now.year}/{str(now.month).zfill(2)}/{str(now.day).zfill(2)} {str(now.hour).zfill(2)}:{str(now.minute).zfill(2)}:{str(now.second).zfill(2)}] '


def log(message: str = '', level: int = 20, end: str = '\n'):
    r'''
    Print a message to stream or file logfile.
    This function adds the current timestamp and supports multi-line printing (split on the "\n" escape character).
    level is the verbosity level with which the message is sent.
    Generally we follow:

        NOTSET   = 0
        DEBUG    = 10
        INFO     = 20
        WARN     = 30
        ERROR    = 40
        CRITICAL = 50
    
    We compare the level against the module-wide log_level variable (by default log_level = 20). If the level is below log_level we do not print it.
    '''
    if level < log_level:
        return

    # dictionaries are handled specially so that they look nice
    if isinstance(message, dict):
        message = json.dumps(message, indent=4, sort_keys=True)

    message = str(message)
    # Print each line separately
    message = message.split('\n')
    for m in message:
        # handle lines that exceed the maximum print width
        if max_width > 0 and len(m) > max_width:
            m = m[:max_width - 4] + ' ...' 

        # add the tab-levels and timestamp
        m = '\t'*tab_level + m
        if print_date:
            m = time_stamp() + m

        print(m, file=logfile, end=end, flush=True)


def flow(message: str = '', tags: List[str] = ['straight'], level: int = 20) -> None:
    '''
    Function to create flowchart-like output.
    It will print a message prepended by flow elements (arrows and lines).
    The flow elements are determined based on the given tags.
    '''
    elements = {
        'start':     '┯ ',
        'startinv':  '┷ ',
        'end':       '╰─> ',
        'straight':  '│   ',
        'split':     '├─> ',
        'skip':      '    ',
        'vert':      '────',
        'endvert':   '╰──> ',
        'splitvert': '├──> ',
    }
    s = ''
    for tag in tags:
        s += elements[tag]
    log(s + message, level=level)


def table(rows: List[List[Any]], header: List[str] = None, sep: str = '   ', hline: List[int] = [], level: int = 20) -> str:
    r'''
    Print a table given rows and a header. Values in rows will be cast to strings first.
    
    Args:
        rows: list of `nrows` sequences containing `ncols` data inside the table.
        header: list of `ncols` strings that represent the column names of the table. They will be printed at the top of the table.
        sep: str representing the separation between columns.
        hline: list of integers specifying rows after which lines will be drawn. Supports negative indices, e.g. -1 will draw a line at the end of the table.

    Returns:
        str: the table in string format, where lines are separated by "\n"
    '''
    rows = ensure_2d(rows)
    nrows = len(rows)
    ncols = len(rows[0])

    hline = [h + nrows + 1 if h < 0 else h for h in hline]

    if header:
        rows = [header] + rows
        hline = [0] + hline

    rows = [[str(x) for x in row] for row in rows]

    column_sizes = [max(len(row[i]) for row in rows) for i in range(ncols)]
    return_str = ''
    for i, row in enumerate(rows):
        row_str = sep.join([x.ljust(column_size) for x, column_size in zip(row, column_sizes)]) + '\n'
        return_str += row_str
        if i in hline:
            return_str += '─' * len(row_str) + '\n'

    log(return_str, level=level)
    return return_str


def loadbar(sequence: Iterable, comment: str = '', Nsegments: int = 50, Nsteps: int = 10, level: int = 20) -> None:
    '''
    Return values from an iterable `sequence` and also print a progress bar for the iteration over this sequence.

    Args:
        sequence: any iterable sequence. Should define the __len__ method.
        comment: a string to be printed at the end of the loading bar to give information about the loading bar.
        Nsegments: length of the loading bar in characters.
        Nsteps: number of times to print the loading bar during iteration. If the output is a tty-type stream Nsteps will be set to the length of sequence.
    '''
    N = len(sequence)
    # if the output stream is tty-type we set the number of steps to the lenth of the sequence so the loading bar looks smoother
    Nsteps = N if logfile.isatty() else Nsteps 
    Ndigits = int(np.log10(N))+1  # well-known method to get number of digits of an integer
    # we track what the maximum length of the loading bar is. 
    # We use the '\r' return carriage when logging, so we have to overwrite the whole previous line. 
    # For this we must know the largest length of our loading bar strings.
    max_length = 0  

    # track when the loading bar started. We use this to calculate the ETA later
    loading_bar_start_time = perf_counter()
    for i, val in enumerate(sequence):
        # we only print the loading bar on every Nsteps iterations
        if i % (N//min(N, Nsteps)) != 0:
            yield val
            continue

        # calculate how many segments should be filled and empty
        Nfilled_segments = int(i/N*Nsegments)
        filled = "─"*Nfilled_segments
        empty = " "*(Nsegments-Nfilled_segments)

        # determine what the cursor should look like
        if Nfilled_segments == Nsegments:  # if the bar is fully filled it should be just a stripe
            cursor = "─"
        elif i == 0:  # if the bar is empty we don't draw the cursor
            cursor = " "
        else:  # normal case
            cursor = ">"

        # calculate the ETA. In the first iteration we cannot know yet
        if i == 0:
            eta = '???'
        else:
            # the algorithm simply extrapolates the current time taken to the case of the final iteration
            time_taken = perf_counter() - loading_bar_start_time
            time_per_step = time_taken/i
            time_left = time_per_step * (N-i)
            eta = f'{time_left:.1f}'

        # build the loading bar string
        s = f'{i:{Ndigits}}/{N} {"├" if i > 0 else "|"}{filled + cursor + empty}{"│"} {i/N:4.0%} {comment} [ETA: {eta}s]'.ljust(max_length)

        # update the max loading bar string length
        max_length = max(len(s), max_length)
        log(s, end='\r', level=level)
    
        yield val

    # plot the final iteration at 100% filled
    s = f'{i+1:{Ndigits}}/{N} {"├"}{"─"*(Nsegments+1)}┤ 100% {comment}'.ljust(max_length)
    log(s, end='\r', level=level)
    log(level=level)


def boxed(message: str, title: str = None, message_align: str = 'left', title_align: str = 'left', round_corners: bool = True, double_edge: bool = False, level: int = 20) -> str:
    r'''
    Print a message surrounded by a box with optional title.

    Args:
        message: the message to place in the box. Multiline messages are separated by "\n".
        title: the title placed in the top edge of the box.
        message_align: alignment of the text inside the box. One of ["left", "center", "right"].
        title_align: alignment of the title. One of ["left", "center", "right"].
        round_corners: whether the corners of the box should be rounded or not. Rounded corners are only available for single-edge boxes.
        double_edge: whether the edges of the box should be double.

    Returns:
        The printed message in strings format.
    '''
    # define the edges and corners
    straights = ['│', '─']
    if round_corners and not double_edge:
        corners = ['╭', '╮', '╯', '╰']
    elif double_edge:
        corners = ['╔', '╗', '╝', '╚']
        straights = ['║', '═']
    else:
        corners = ['┌', '┐', '┘', '└']

    # get the width the box should have
    messages = message.split('\n')
    # the length is influenced by both the messages as well as the title
    maxlen = max(
        max(len(message) for message in messages), 
        len(title or '')
        )

    # build first row containing the title
    if title is not None:
        if title_align == 'left':
            s = corners[0] + (' ' + title + ' ').ljust(maxlen+2, straights[1]) + corners[1] + '\n'
        elif title_align == 'right':
            s = corners[0] + (' ' + title + ' ').rjust(maxlen+2, straights[1]) + corners[1] + '\n'
        else:
            s = corners[0] + (' ' + title + ' ').center(maxlen+2, straights[1]) + corners[1] + '\n'
    else:
        s = corners[0] + straights[1]*(maxlen+2) + corners[1] + '\n'

    # build main body of box
    for message in messages:
        if message_align == 'left':
            s += f'{straights[0]} ' + message.ljust(maxlen) + f' {straights[0]}\n'
        if message_align == 'right':
            s += f'{straights[0]} ' + message.rjust(maxlen) + f' {straights[0]}\n'
        if message_align == 'center':
            s += f'{straights[0]} ' + message.center(maxlen) + f' {straights[0]}\n'

    # build bottom row
    s += corners[3] + straights[1]*(maxlen+2) + corners[2]

    log(s, level=level)


def info(message, level=20):
    '''
    Display informative message using the boxed function.
    '''
    boxed(message, round_corners=True, double_edge=False, title='Info', level=level)


def warn(message, level=30):
    '''
    Display a warning message using the boxed function.
    '''
    boxed(message, double_edge=True, title='Warning', title_align='center', level=level)


if __name__ == '__main__':
    boxed('testing, 1, 2, 3, 4, 5, 6, 7, 8\nsecond row, 1, 2, 3, 4, 5, 6\n...\n...\n\n...\n...\nLast row here', title='ReactionRunner')

    with NoPrint():
        log('test test test')
        log('test test test')
        log('test test test')
        log('test test test')

    log()

    flow('Start', ['start'])
    flow()
    flow('First step', ['split'])
    flow('First substep of first step', ['straight', 'split'])
    flow('Second substep of first step', ['straight', 'split'])
    flow('Third and final substep of first step', ['straight', 'end'])
    flow()
    flow('Second step', ['split'])
    flow('Substep of second step', ['straight', 'split'])
    flow('Substep of substep of second step', ['straight', 'straight', 'end'])
    flow('Substep of substep of substep of second step', ['straight', 'straight', 'skip', 'end'])
    flow('Substep of second step', ['straight', 'end'])
    flow()
    flow('Final step', ['split'])
    flow()
    flow(f'{Emojis.good} The end', ['startinv'])

    log()

    info('This is important info')
    warn('This is an important warning!')

    import time
    for x in loadbar(range(100), 'Sleeping test'):
        time.sleep(.01)

    x = np.linspace(1, 12, 12)
    rows = np.vstack([x, x**2, x**3, x**4, x**5]).astype(int).T.tolist()
    table(rows, header=['X', 'y=x^2', 'y=x^3', 'y=x^4', 'y=x^5'], hline=[-1])
