import sys
import os
from datetime import datetime
from time import perf_counter
import numpy as np
import json
from tcutility import ensure_2d
from typing import Any, Iterable, List, Union
from types import GeneratorType
import inspect
# from threading import Thread


###########################################################
# MODULE LEVEL VARIABLES USED TO CHANGE LOGGING BEHAVIOUR #
logfile = sys.stdout  # stream or file to send prints to. Default sys.stdout is the standard Python print output
errfile = sys.stderr  # stream or file to send prints to. Default sys.stderr is the standard Python print output
tab_level = 0  # number of tabs to add before a logged message. This is useful to build a sense of structure in a long output
max_width = 0  # maximum width of printed messages. Default 0 means unbounded
print_date = True  # print time stamp before a logged message
log_level = 20  # the level of verbosity. Messages with a log_level >= this number will be sent to logfile


class Emojis:
    """
    Class containing some useful emojis and other characters.
    Supports dot-notation and indexation to get a character.

    E.g. ``Emojis.wait == Emojis['wait']``
    """

    wait = "🕒"
    good = "✅"
    cancel = "🛑"
    sleep = "💤"
    fail = "❌"
    send = "📤"
    receive = "📥"
    empty = "⠀⠀"
    finish = "🏁"
    warning = "⚠️"
    question = "❔"
    info = "ℹ️"
    rarrow = "─>"
    larrow = "<─"
    lrarrow = rlarrow = "<─>"
    angstrom = "Å"

    def __init__(self):
        raise SyntaxError("Do not instantiate the Emojis-class.")

    def __class_getitem__(cls, item):
        return getattr(cls, item)


class NoPrint:
    """
    Context-manager that suppresses printing. It works by redirecting prints to a temporary output file.
    This file is deleted after exiting the context-manager.
    """

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout or logfile
        self.stderr = stderr or errfile
        self.overflow = open(str(os.getpid()) + "_NOPRINT.tmp", "w+")

    def __enter__(self):
        global logfile, errfile
        logfile = self.overflow
        errfile = self.overflow

    def __exit__(self, *args, **kwargs):
        global logfile, errfile
        logfile = self.stdout
        errfile = self.stderr
        self.overflow.close()
        os.remove(str(os.getpid()) + "_NOPRINT.tmp")


def time_stamp():
    """
    Return the current timestamp in a "[YYYY/MM/DD HH:MM:SS] "" format.
    """
    now = datetime.now()
    return f"[{now.year}/{str(now.month).zfill(2)}/{str(now.day).zfill(2)} {str(now.hour).zfill(2)}:{str(now.minute).zfill(2)}:{str(now.second).zfill(2)}] "


def log(message: Any = "", level: int = 20, end: str = "\n"):
    r"""
    Print a nicely formatteed message.
    This function adds the current timestamp and supports multi-line printing (split on the ``\n`` escape character).
    For verbosity levels we use the following convention:

    .. code-block::

        NOTSET   = 0
        DEBUG    = 10
        INFO     = 20
        WARN     = 30
        ERROR    = 40
        CRITICAL = 50

    
    Args:
        message: the message to send. Before printing we will use the ``message.__str__`` method to get the string representation. If the message is a ``dict`` we use the ``json`` module to format the message nicely.
        level: the level to print the message at. We compare the level against the module-wide ``log_level`` variable (by default ``log_level = 20``). If the level is below ``log_level`` we do not print it.
        end: the end of the string. This is usually the new-line character ``\n``.
    """
    if level < log_level:
        return

    # dictionaries are handled specially so that they look nice
    if isinstance(message, dict):
        message = json.dumps(message, indent=4, sort_keys=True)

    # Print each line separately
    splitted_message = str(message).split("\n")
    for m in splitted_message:
        # handle lines that exceed the maximum print width
        if max_width > 0 and len(m) > max_width:
            m = m[: max_width - 4] + " ..."

        # add the tab-levels and timestamp
        m = "\t" * tab_level + m
        if print_date:
            m = time_stamp() + m

        print(m, file=logfile, end=end, flush=True)


def flow(message: str = "", tags: List[str] = ["straight"], level: int = 20) -> None:
    """
    Function to create flowchart-like output.
    It will print a message prepended by flow elements (arrows and lines).
    The flow elements are determined based on the given tags.
    """
    elements = {
        "start": "┯ ",
        "startinv": "┷ ",
        "end": "╰─> ",
        "straight": "│   ",
        "split": "├─> ",
        "skip": "    ",
        "vert": "────",
        "endvert": "╰──> ",
        "splitvert": "├──> ",
    }
    s = ""
    for tag in tags:
        s += elements[tag]
    log(s + message, level=level)


def table(rows: List[List[Any]], header: Union[List[str], None] = None, sep: str = "   ", hline: List[int] = [], level: int = 20) -> str:
    r"""
    Print a table given rows and a header. Values in rows will be cast to strings first.

    Args:
        rows: list of `nrows` sequences containing `ncols` data inside the table.
        header: list of `ncols` strings that represent the column names of the table. They will be printed at the top of the table.
        sep: str representing the separation between columns.
        hline: list of integers specifying rows after which lines will be drawn. Supports negative indices, e.g. -1 will draw a line at the end of the table.

    Returns:
        str: the table in string format, where lines are separated by "\n"
    """
    rows = ensure_2d(rows)
    nrows = len(rows)
    ncols = len(rows[0])

    hline = [h + nrows + 1 if h < 0 else h for h in hline]

    if header:
        rows = [header] + rows
        hline = [0] + hline

    rows = [[str(x) for x in row] for row in rows]

    column_sizes = [max(len(row[i]) for row in rows) for i in range(ncols)]
    return_str = ""
    for i, row in enumerate(rows):
        row_str = sep.join([x.ljust(column_size) for x, column_size in zip(row, column_sizes)]) + "\n"
        return_str += row_str
        if i in hline:
            return_str += "─" * len(row_str) + "\n"

    log(return_str, level=level)
    return return_str


def rectangle_list(values: List, spaces_before: int = 0, level: int = 20):
    '''
    This function prints a list of strings in a rectangle to the output.
    This is similar to what the ls program does in unix.
    '''
    n_shell_col = os.get_terminal_size().columns
    # we first have to determine the correct dimensions of our rectangle
    for ncol in range(1, n_shell_col):
        # the number of rows for the number of columns
        nrows = ceil(len(values) / ncol)
        # we then get what the rectangle would be
        mat = [str(values[i * ncol: (i+1) * ncol]) for i in range(nrows)]
        # and determine for each column the width
        col_lens = [max([len(row[i]) for row in mat if i < len(row)] + [0]) for i in range(ncol)]
        # then calculate the length of each row based on the column lengths
        # we use a spacing of 2 spaces between each column
        row_len = spaces_before + sum(col_lens) + 2 * len(col_lens) - 2

        # if the rows are too big we exit the loop
        if row_len > n_shell_col:
            break

        # store the previous loops results
        prev_col_lens = col_lens
        prev_mat = mat

    # then print the strings with the right column widths
    for row in prev_mat:
        log(" " * spaces_before + "  ".join([x.ljust(col_len) for x, col_len in zip(row, prev_col_lens)]))


def loadbar(sequence: Iterable, comment: str = "", Nsegments: int = 50, Nsteps: int = 10, level: int = 20) -> None:
    """
    Return values from an iterable ``sequence`` and also print a progress bar for the iteration over this sequence.

    Args:
        sequence: any iterable sequence. Should define the ``__len__`` method.
        comment: a string to be printed at the end of the loading bar to give information about the loading bar.
        Nsegments: length of the loading bar in characters.
        Nsteps: number of times to print the loading bar during iteration. If the output is a tty-type stream Nsteps will be set to the length of sequence.
    """
    if isinstance(sequence, GeneratorType):
        chars = ["⠀", "⠄", "⠆", "⠦", "⠧", "⠷", "⠿", "⠻", "⠛", "⠙", "⠉", "⠈", "⠀"]
        iteration = 0
        if not logfile.isatty() and comment:
            log(comment, level=level)

        starttime = perf_counter()
        for val in sequence:
            iteration += 1
            elapsed_time = (perf_counter() - starttime)
            time_per_step = elapsed_time / iteration
            # every 0.1 seconds we change the character
            char_step = int(elapsed_time / 0.1) % len(chars)
            if logfile.isatty():
                log(f'{chars[char_step]} {comment} [Steps: {iteration}, Elapsed: {elapsed_time:.1f}s]', end="\r", level=level)

            yield val

        log(level=level)
        return

    N = len(sequence)
    # if the output stream is tty-type we set the number of steps to the lenth of the sequence so the loading bar looks smoother
    Nsteps = N if logfile.isatty() else Nsteps
    Ndigits = int(np.log10(N)) + 1  # well-known method to get number of digits of an integer
    # we track what the maximum length of the loading bar is.
    # We use the '\r' return carriage when logging, so we have to overwrite the whole previous line.
    # For this we must know the largest length of our loading bar strings.
    max_length = 0

    # track when the loading bar started. We use this to calculate the ETA later
    loading_bar_start_time = perf_counter()
    for i, val in enumerate(sequence):
        # we only print the loading bar on every Nsteps iterations
        if i % (N // min(N, Nsteps)) != 0:
            yield val
            continue

        # calculate how many segments should be filled and empty
        Nfilled_segments = int(i / N * Nsegments)
        filled = "─" * Nfilled_segments
        empty = " " * (Nsegments - Nfilled_segments)

        # determine what the cursor should look like
        if Nfilled_segments == Nsegments:  # if the bar is fully filled it should be just a stripe
            cursor = "─"
        elif i == 0:  # if the bar is empty we don't draw the cursor
            cursor = " "
        else:  # normal case
            cursor = ">"

        # calculate the ETA. In the first iteration we cannot know yet
        if i == 0:
            eta = "???"
        else:
            # the algorithm simply extrapolates the current time taken to the case of the final iteration
            time_taken = perf_counter() - loading_bar_start_time
            time_per_step = time_taken / i
            time_left = time_per_step * (N - i)
            eta = f"{time_left:.1f}"

        # build the loading bar string
        s = f'{i:{Ndigits}}/{N} {"├" if i > 0 else "|"}{filled + cursor + empty}{"│"} {i/N:4.0%} {comment} [ETA: {eta}s]'.ljust(max_length)

        # update the max loading bar string length
        max_length = max(len(s), max_length)
        log(s, end="\r", level=level)

        yield val

    # plot the final iteration at 100% filled
    s = f'{i+1:{Ndigits}}/{N} {"├"}{"─"*(Nsegments+1)}┤ 100% {comment}'.ljust(max_length)
    log(s, end="\r", level=level)
    log(level=level)


def boxed(message: str, title: Union[str, None] = None, message_align: str = "left", title_align: str = "left", round_corners: bool = True, double_edge: bool = False, level: int = 20) -> str:
    r"""
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
    """
    # define the edges and corners
    straights = ["│", "─"]
    if round_corners and not double_edge:
        corners = ["╭", "╮", "╯", "╰"]
    elif double_edge:
        corners = ["╔", "╗", "╝", "╚"]
        straights = ["║", "═"]
    else:
        corners = ["┌", "┐", "┘", "└"]

    # get the width the box should have
    messages = message.split("\n")
    # the length is influenced by both the messages as well as the title
    maxlen = max(max(len(message) for message in messages), len(title or ""))

    # build first row containing the title
    if title is not None:
        if title_align == "left":
            s = corners[0] + (" " + title + " ").ljust(maxlen + 2, straights[1]) + corners[1] + "\n"
        elif title_align == "right":
            s = corners[0] + (" " + title + " ").rjust(maxlen + 2, straights[1]) + corners[1] + "\n"
        else:
            s = corners[0] + (" " + title + " ").center(maxlen + 2, straights[1]) + corners[1] + "\n"
    else:
        s = corners[0] + straights[1] * (maxlen + 2) + corners[1] + "\n"

    # build main body of box
    for message in messages:
        if message_align == "left":
            s += f"{straights[0]} " + message.ljust(maxlen) + f" {straights[0]}\n"
        if message_align == "right":
            s += f"{straights[0]} " + message.rjust(maxlen) + f" {straights[0]}\n"
        if message_align == "center":
            s += f"{straights[0]} " + message.center(maxlen) + f" {straights[0]}\n"

    # build bottom row
    s += corners[3] + straights[1] * (maxlen + 2) + corners[2]

    log(s, level=level)


def debug(message: str, level: int = 10, caller_level: int = 2):
    """
    Print a debug message.
    """
    log(f"[DEBUG]({caller_name(caller_level)}): " + message, level=level)


def info(message: str, level: int = 20, caller_level: int = 2):
    """
    Print an informative message.
    """
    log(f"[INFO]({caller_name(caller_level)}): " + message, level=level)


def warn(message: str, level: int = 30, caller_level: int = 2):
    """
    Print a warning message.
    """
    log(f"[WARNING]({caller_name(caller_level)}): " + message, level=level)


def error(message: str, level: int = 40, caller_level: int = 2):
    """
    Print an error message.
    """
    log(f"[ERROR]({caller_name(caller_level)}): " + message, level=level)


def critical(message: str, level: int = 50, caller_level: int = 2):
    """
    Print a critical message.
    """
    log(f"[CRITICAL]({caller_name(caller_level)}): " + message, level=level)


def caller_name(level: int = 1) -> str:
    """
    Return the full name of the caller of a function.

    Args:
        level: the number of levels to skip when getting the caller name. Level 1 is always this function. When used by a different function it should be set to 2. E.g. when using the log.warn function level is set to 2.

    Returns:
        The full name of the caller function.
    """
    stack = inspect.stack()
    names = [stack[level][3]]  # add the original function, this should be at a certain levels, since this function is called by warn or info or error
    for frame in stack[level:]:
        if frame.function == "<module>":  # <module> is always there, so we can skip it
            continue

        # get the more interesting names
        # first check if the
        if hasattr(frame[0], "f_locals") and "self" in frame[0].f_locals:
            clas = frame[0].f_locals["self"].__class__
            module = clas.__module__
            if module == "builtins":
                names.append(clas.__qualname__)
            else:
                names.append(module + "." + clas.__qualname__)
        elif hasattr(frame[0], "f_code"):
            names.append(frame[0].f_code.co_name)
    names_ordered = []
    for name in names[::-1]:
        if name not in names_ordered:
            names_ordered.append(name)
    return ".".join(names_ordered)


if __name__ == "__main__":
    boxed("testing, 1, 2, 3, 4, 5, 6, 7, 8\nsecond row, 1, 2, 3, 4, 5, 6\n...\n...\n\n...\n...\nLast row here", title="ReactionRunner")

    with NoPrint():
        log("test test test")
        log("test test test")
        log("test test test")
        log("test test test")

    log()

    flow("Start", ["start"])
    flow()
    flow("First step", ["split"])
    flow("First substep of first step", ["straight", "split"])
    flow("Second substep of first step", ["straight", "split"])
    flow("Third and final substep of first step", ["straight", "end"])
    flow()
    flow("Second step", ["split"])
    flow("Substep of second step", ["straight", "split"])
    flow("Substep of substep of second step", ["straight", "straight", "end"])
    flow("Substep of substep of substep of second step", ["straight", "straight", "skip", "end"])
    flow("Substep of second step", ["straight", "end"])
    flow()
    flow("Final step", ["split"])
    flow()
    flow(f"{Emojis.good} The end", ["startinv"])

    log()

    info("This is important info")
    warn("This is an important warning!")

    import time

    for x in loadbar(range(100), "Sleeping test"):
        time.sleep(0.01)

    x = np.linspace(1, 12, 12)
    rows = np.vstack([x, x**2, x**3, x**4, x**5]).astype(int).T.tolist()
    table(rows, header=["X", "y=x^2", "y=x^3", "y=x^4", "y=x^5"], hline=[-1])

    from tcutility import log

    class TestClass:
        def test_method(self):
            log.warn("I am testing the warning function")

    TestClass().test_method()
