import os
from enum import Enum, auto
from tcutility import connect


class OSName(Enum):
    """
    An enumeration of the different operating systems.
    """

    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()


def get_os_name(server: connect.Server = connect.Local()) -> OSName:
    """
    Get the name of the operating system. Returns a value from the :class:`OSName <tcutility.environment.OSName>` enumeration.
    """
    # if we are connected to a server we are on linux
    if not isinstance(server, connect.Local):
        return OSName.LINUX

    os_name = os.name
    if os_name == "nt":
        return OSName.WINDOWS
    elif os_name == "posix":
        return OSName.LINUX
    elif os_name == "mac":
        return OSName.MACOS
    else:
        raise ValueError(f"Unknown operating system: {os_name}")
