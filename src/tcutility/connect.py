import atexit
import os
import platform
import shutil
import subprocess as sp
import uuid
from datetime import datetime
from enum import Enum, auto

from tcutility import environment, log
import tcutility.cache as cache
from tcutility.results import result as results


class OSName(Enum):
    """
    An enumeration of the different operating systems.
    """

    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()


_open_connections = []


class Connection:
    """
    Main class used for creating and using SSH sessions to remote servers.
    It gives you the option to execute any shell code, but also provides useful default commands (for example, ``cd`` and ``ls``).
    The ``Connection`` class also allows you to download and upload files between your local machine and the remote.

    Args:
        server: the adress of the server you want to connect to. You can prepend the server adress with your username separated from the adress with a ``@`` character.
            For example: ``Connection('username@server.address.nl')`` is the same as ``Connection('server.address.nl', 'username')``.
        username: the username used to log in to the remote server.
        key_filename: if you cannot log in using only the ``ssh`` command you can try to give the
            filename of the private key that matches a public key on the server.

    Usage:
        This class is a context manager and the ``with``-syntax should be used to open and automatically close connections.
        For example, to open a connection to the Snellius supercomputer we use the following code:

        .. code-block::

            from tcutility.connect import Connection

            with Connection('username@server.address.nl') as server:
                print(server.pwd())  # this will print the home-directory of the logged-in user
                server.cd('example/path/to/some/data')
                print(server.pwd())  # ~/example/path/to/some/data

    .. warning::
        Currently we only support logging in using SSH keys. Make sure that you can log in to the remote with SSH keys.
        There might be server specific instructions on how to enable this authentication method.
    """

    def __init__(self, server: str = None, username: str = None, key_filename: str = None):
        if server is not None:
            self.server = server

        if username is not None:
            self.username = username

        if server is not None and "@" in server:
            self.username, self.server = server.split("@")

        self.key_filename = key_filename
        if isinstance(key_filename, str):
            self.key_filename = os.path.abspath(os.path.expanduser(key_filename))

    def open(self):
        self.__enter__()

    @environment.requires_optional_package("paramiko")
    def __enter__(self):
        import paramiko

        log.debug(f"{self}: opening connection ...")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.server, username=self.username, key_filename=self.key_filename)
        log.debug(f"{self}: connection opened!")
        # store the home directory so we can use it later to get absolute paths
        self.home = self.client.exec_command("pwd")[1].read().decode().strip()
        self.currdir = self.home
        _open_connections.append(self)
        return self

    def close(self):
        self.__exit__()

    def __exit__(self, *args, **kwargs):
        _open_connections.remove(self)
        self.client.close()
        log.debug(f"{self}: connection closed.")

    def __repr__(self):
        return f"Connection({self.username}@{self.server})"

    def full_path(self, path: str) -> str:
        if path.startswith("/"):
            return path
        return os.path.join(self.currdir, path)

    def execute(self, command: str) -> str:
        """
        Run a command on the server and return the output.

        Args:
            command: the command to run on the server.

        Returns:
            Data written in ``stdout`` after the command was run.

        Raises:
            ``RuntimeError`` with error message if there was something printed to the ``stderr``.

        .. note::
            The ``__call__`` method redirects to this method. This means you can directly call the ``Connection`` object with your command.
        """
        log.debug(f"{self}[{self.currdir}]: {command}")
        command = f"cd {self.currdir}; {command}"
        _, stdout, stderr = self.client.exec_command(command)
        stdout = stdout.read().decode()
        stderr = stderr.read().decode()
        if stderr:
            raise RuntimeError(stderr)

        return stdout.strip()

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def ls(self, path="") -> results.Result:
        """
        Run the ``ls`` program and return useful information about the paths.

        Args:
            path: the path to run ls on.

        Returns:
            :Result object containing information from the output of the ``ls`` program.
                The keys are the path names and the values contain the information.

                - **owner (str)** - the username of the owner of the path.
                - **date (datetime.datetime)** - ``datetime`` object holding the date the file was created.
                - **is_dir (bool)** - whether the path is a directory.
                - **is_hidden (bool)** - whether the path is hidden.
                - **permissions (str)** - the permissions given to the path.
        """
        out = self.execute(f'TZ="UTC" ls -lAFp --full-time {path}')
        lines = out.splitlines()
        ret = results.Result()
        for line in lines[1:]:  # first line is a total count
            parts = line.split()
            name = parts[-1]
            is_dir = False
            if name.endswith("/"):
                is_dir = True
                name = name[:-1]

            ret[name].is_dir = is_dir

            timestamp = " ".join(parts[5:7])
            ret[name].date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f000")
            ret[name].owner = parts[2]
            ret[name].is_hidden = name.startswith(".")
            ret[name].permissions = parts[0]

        return ret

    def cd(self, path="~"):
        """
        Run the ``cd`` command.

        Args:
            path: the path to change directories to. This is relative to the current directory.

        .. note::
            Due to limitations with some servers (e.g. Snellius) we do not actually run the ``cd`` command,
            but update the internal ``Connection.currdir`` attribute. Before running any command we prepend with ``cd {self.currdir}; ...``.
            In this way we run commands from the correct directory.
        """
        log.debug(f"{self}[{self.currdir}]: cd {path}")
        path = path.replace("~", self.home)
        if path.startswith("/"):
            self.currdir = path
        else:
            self.currdir = os.path.normpath(os.path.join(self.currdir, path))

    def pwd(self) -> str:
        """
        Run the ``pwd`` command.

        .. note::
            Due to limitations with some servers (e.g. Snellius) we do not actually run the ``pwd`` command,
            instead we return the internal ``Connection.currdir`` attribute. See the :func:`Connection.cd` method for more details.
        """
        log.debug(f"{self}[{self.currdir}]: pwd")
        return self.currdir

    def mkdir(self, dirname):
        """
        Run the ``mkdir`` command.

        Args:
            dirname: the name of the directory to make. This is relative to the current directory.
        """
        self.execute(f"mkdir -p {dirname}")

    def rm(self, file_path):
        self.execute(f"rm {file_path}")

    def rmtree(self, dirname):
        self.execute(f"rm -r {dirname}")

    def download(self, server_path: str, local_path: str):
        """
        Download a file from the server and store it on your local machine.

        Args:
            server_path: the path on the server to the file to download. The path is relative to the current directory.
            local_path: the path on the local machine where the file is stored.
        """
        server_path = os.path.normpath(self.full_path(server_path))

        log.debug(f"{self}: download {server_path} {local_path}")
        with self.client.open_sftp() as sftp:
            sftp.get(server_path, local_path)
        log.debug(f"{self}: download completed!")

    def upload(self, local_path: str, server_path: str = None):
        """
        Upload a file from your local machine to the server.
        If the ``server_path`` is not given, store it in the current directory.

        Args:
            local_path: the path on the local machine where the file to be uploaded is stored.
            server_path: the path to upload the file to.
                If not given or set to ``None`` we upload the file to the current directory with the same filename.
        """
        if server_path is None:
            server_path = os.path.join(self.currdir, os.path.basename(local_path))
        elif not server_path.startswith("/"):
            server_path = os.path.join(self.currdir, server_path)
        server_path = os.path.normpath(server_path)

        log.debug(f"{self}: upload {local_path} {server_path}")
        with self.client.open_sftp() as sftp:
            sftp.put(local_path, server_path)
        log.debug(f"{self}: upload completed!")

    def path_exists(self, path: str):
        test = self.execute(f"test -e {path}; echo $?")
        return test == "0"

    def open_file(self, file_path: str, mode: str = "w+"):
        return ServerFile(file_path, self, mode)

    def chmod(self, rights: int, file_path: str):
        self.execute(f"chmod {rights} {file_path}")


class ServerFile:
    def __init__(self, file_path: str, server: Connection, mode: str = "w+"):
        self.server = server
        self.file_path = file_path
        self.tmp_path = str(uuid.uuid4())
        self.file = open(self.tmp_path, mode=mode)

    def __enter__(self):
        return self.file

    def __exit__(self, *args):
        self.file.close()
        self.server.upload(self.tmp_path, self.file_path)
        os.remove(self.tmp_path)


class Server(Connection):
    """
    Helper subclass of :class:``Connection`` that is used to quickly connect to a specific server.
    The constructor takes only the username as the server url is already set. You can also specify
    default settings for ``sbatch`` calls, for example the partition or time-limits.
    """

    server = None
    sbatch_defaults = {}
    preamble_defaults = {}
    postamble_defaults = {}
    program_modules = {}

    def __init__(self, username=None):
        super().__init__(self.server, username=username)

    def __repr__(self):
        return f"{type(self).__name__}({self.username})"


class Local(Server):
    server = None
    sbatch_defaults = {}
    preamble_defaults = {}
    postamble_defaults = {}
    program_modules = {}
    home = '~'

    def __init__(self):
        self.currdir = os.getcwd()

    def __enter__(self):
        return self

    def __exit__(self, *args): ...

    def execute(self, command: str) -> str:
        """
        Execute a command on the local machine and return the output.

        Args:
            command: the command to run.

        .. note::
            We use ``subprocess.check_output`` with the ``shell=True`` argument enabled.
        """
        try:
            output = sp.check_output(command, shell=True).decode()
            return output
        except sp.CalledProcessError:
            print("COMMAND: ", command)
            raise

    def mkdir(self, dirname):
        os.makedirs(os.path.join(self.currdir, dirname), exist_ok=True)

    def rm(self, file_path):
        os.remove(file_path) if os.path.exists(file_path) else ...

    def rmtree(self, dirname):
        shutil.rmtree(dirname) if os.path.exists(dirname) else ...

    def download(self, server_path: str, local_path: str):
        shutil.copy2(os.path.join(self.currdir, server_path), os.path.join(self.currdir, local_path))

    def upload(self, local_path: str, server_path: str = None):
        shutil.copy2(os.path.join(self.currdir, local_path), os.path.join(self.currdir, server_path))

    def path_exists(self, path: str) -> bool:
        return os.path.exists(os.path.join(self.currdir, path))

    def open_file(self, file_path: str, mode: str = 'w+'):
        return open(file_path, mode=mode)

    def chmod(self, rights: int, path: str):
        os.chmod(os.path.join(self.currdir, path), int(str(rights), base=8))

    def pwd(self):
        return os.getcwd()

    def ls(self, dirname):
        return os.listdir(dirname)


class Ada(Server):
    """
    Default set-up for a connection to the Ada cluster. By default we use the ``tc`` partition.
    """

    server = "ada.labs.vu.nl"
    sbatch_defaults = {
        "p": "tc",
        "ntasks_per_node": 16,
        "N": 1,
        "mem": 250000,
    }
    preamble_defaults = {
        "AMS": [
            'export SCM_TMPDIR="/scratch/$SLURM_JOBID"',
            "srun mkdir -p $SCM_TMPDIR",
            "chmod 700 $SCM_TMPDIR",
        ]
    }
    program_modules = {
        "AMS": {
            "2021": "module load shared ams/2021.102",
            "2022": "module load shared ams/2022.103",
            "2023": "module load shared ams/2023.101",
            "2024": "module load shared ams/2024.102",
            "latest": "module load shared ams/2024.102",
        }
    }
    postamble_defaults = {
        "AMS": [
            "srun rm -rf $SCM_TMPDIR",
        ]
    }


class Snellius(Server):
    """
    Default set-up for a connection to the Snellius cluster. By default we use the ``rome`` partition and a time-limit set to ``120:00:00``.
    """

    server = "snellius.surf.nl"
    sbatch_defaults = {
        "p": "rome",
        "t": "120:00:00",
        "ntasks_per_node": 16,
        "N": 1,
    }
    program_modules = {
        "AMS": {
            "2023": "module load 2023 AMS/2023.104-intelmpi",
            "2024": "module load 2024 AMS/2024.104-intelmpi-aocl",
            "latest": "module load 2024 AMS/2024.104-intelmpi-aocl",
        }
    }


@cache
def get_current_server() -> Server:
    """
    Return the `Server`-subclass of the server location of the current shell.
    If the server location could not be detected returns `Local`.
    """
    ifconfig = sp.check_output("ifconfig")
    parts = ifconfig.decode().split()
    adresses = []
    for i, part in enumerate(parts):
        if part == "inet":
            adresses.append(parts[i + 1].split(".")[:3])

    # print(ifconfig)
    for cls in Server.__subclasses__():
        if cls is Local:
            continue
            
        ping = sp.check_output(["ping", cls.server, "-c", "1"])

        for part in ping.decode().split():
            if part.startswith("(") and part.endswith("):"):
                ip_address = part[1:-2].split(".")[:3]
                if ip_address in adresses:
                    return cls
    return Local


def _close_all_connections():
    for conn in _open_connections:
        conn.__exit__()


atexit.register(_close_all_connections)


def get_os_name(server: Server = Local()) -> OSName:
    """
    Get the name of the operating system. Returns a value from the :class:`OSName <tcutility.environment.OSName>` enumeration.
    """
    # if we are connected to a server we are on linux
    if not isinstance(server, Local):
        return OSName.LINUX

    os_name = platform.system()
    if os_name == "Windows":
        return OSName.WINDOWS
    elif os_name == "Linux":
        return OSName.LINUX
    elif os_name == "Darwin":
        return OSName.MACOS
    else:
        raise ValueError(f"Unknown operating system: {os_name}")


@cache
def on_windows(server: Server = Local()) -> bool:
    return get_os_name(server) == OSName.WINDOWS

@cache
def on_linux(server: Server = Local()) -> bool:
    return get_os_name(server) == OSName.LINUX

@cache
def on_macos(server: Server = Local()) -> bool:
    return get_os_name(server) == OSName.MACOS


if __name__ == "__main__":
    print(get_current_server())
    print(get_os_name())
