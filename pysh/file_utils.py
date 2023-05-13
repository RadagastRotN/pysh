import os
import re
import shutil
from pathlib import Path

import psutil

from .generator import make_source, make_pipe
from .main import Flags, NO_FLAGS

_working_dir = os.path.abspath(os.path.curdir)
_prev_working_dir = _working_dir


def rm(file_path, flags=NO_FLAGS):
    """
    Removes specified file or empty directory
    With flag R also removes non-empty directory with all content
    F - ignore missing files
    """
    file_path = _to_absolute(file_path)
    if not os.path.exists(file_path) and Flags.F not in flags:
        raise FileNotFoundError()
    elif file_path.is_file():
        os.remove(file_path)
    elif file_path.is_dir():
        if not os.listdir(file_path):
            os.rmdir(file_path)
        elif Flags.R not in flags:
            raise IsADirectoryError("{} is a directory and is not empty. If you want to remove it, specify the R flag.")
        else:
            shutil.rmtree(file_path)


@make_source
def ls(flags=NO_FLAGS, dirname=None, only_dirs=False, only_files=False):
    """
    Lists all subdirectories and files in given directory (if None, then lists current directory)
    Flags:
    R - recursively also list content of subdirectories
    Params:
    only_dirs - list subdirectories onlu
    only_files - list only files, ommiting subdiretories and special files (links, pipes and so on)
    """
    if type(flags) is str and dirname is None:
        dirname, flags = flags, NO_FLAGS
    if dirname is None:
        dirname = _working_dir
    if Flags.R not in flags:
        for dirpath, dirnames, filenames in os.walk(dirname):
            if not only_files:
                yield from dirnames
            if not only_dirs:
                yield from filenames
            break
    else:
        for dirpath, dirnames, filenames in os.walk(dirname):
            if not only_files:
                yield from dirnames
            if not only_dirs:
                yield from (os.path.join(dirpath, fname) for fname in filenames)


class cd:
    """
    Changes the working directory
    cd("-") changes it back to the previous one
    Also works as context manager
    """

    def __init__(self, dirname):
        global _working_dir, _prev_working_dir  # yes, I know
        old_working_dir = _working_dir
        self.old_prev_working_dir = _prev_working_dir  # in order to restore it if cd is used as a context manager

        if dirname == "-":
            _working_dir, _prev_working_dir = _prev_working_dir, _working_dir
        else:
            _prev_working_dir = _working_dir
            self._previous_dir = _working_dir

            abs_dir = os.path.abspath(os.path.join(_working_dir, dirname))
            if abs_dir == dirname:
                _working_dir = dirname
            else:
                for next_dir in os.path.normpath(dirname).split(os.path.sep):
                    if next_dir in ls(only_dirs=True) or next_dir in [os.path.pardir, os.path.curdir]:
                        _working_dir = os.path.join(_working_dir, next_dir)
                    else:
                        raise FileNotFoundError("No such directory {} in {}".format(next_dir, _working_dir))
        if _working_dir != old_working_dir:
            os.chdir(_working_dir)

    def __enter__(self):
        global _prev_working_dir
        _prev_working_dir = self.old_prev_working_dir
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _working_dir  # yes, I know
        _working_dir = self._previous_dir
        return False


def pwd():
    """Returns current working directory"""
    return _working_dir


def touch(filename):
    """Touches the file - if it doesn't exist creates it, and if it does updates the access time"""
    _to_absolute(filename).touch(exist_ok=True)


def mkdir(dirname):
    """Creates directory given either by absolute or relative path"""
    _to_absolute(dirname).mkdir(parents=True, exist_ok=True)


def df(partition=None):
    """Returns the list of mounted partitions with total size, used space and free space"""
    for part in psutil.disk_partitions(all=True):
        try:
            if (partition is None or part.mountpoint == partition or part.device == partition) and not (
                    "/snap" in part.mountpoint or part.mountpoint.startswith(
                "/sys") or part.mountpoint.startswith("/proc")):
                part_usage = psutil.disk_usage(part.mountpoint)
                if part_usage.total:
                    yield part.device, part.mountpoint, part_usage.total, part_usage.used, part_usage.free
        except PermissionError:
            continue  # skipping this partition


def du(path):
    """Calculates disk usage by given file or directory"""
    path = Path(path)
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        for _, subdirs, files in os.walk(path):
            return sum(du(path / subpath) for subpath in subdirs + files)
    else:
        return 0


def cp(source, dest, flags=NO_FLAGS):
    """
    Copies given source file to dest file
    If source file is directory flag R (recursive) must be specified
    """
    source = _to_absolute(source)
    dest = _to_absolute(dest)
    if source.is_dir() and Flags.R in flags:
        shutil.copytree(source, dest)
    else:
        shutil.copy(source, dest)


def mv(source, dest):
    """Moves source file or directory to dest"""
    source = _to_absolute(source)
    dest = _to_absolute(dest)
    shutil.move(source, dest)


def find(path, name="", file_type=None, skip_hidden=False):
    """
    Finds files on disk using given criteria.
    Criteria may include:
    name - matches if the filename contains given string or matches given regex;
    filetype - f for regular file, d for directory, l for link;
    """

    @make_pipe
    def filter_name(source, pattern):
        if 'match' not in dir(pattern):
            pattern = re.compile(pattern)
        yield from (fname for fname in source if pattern.match(os.path.split(fname)[-1]))

    @make_pipe
    def filter_filetype(source, ftype):
        func = {"dir": os.path.isdir, "file": os.path.isfile, "link": os.path.islink}[ftype]
        yield from (fname for fname in source if func(fname))

    @make_source
    def find_all(path, filter_hidden=False):
        path = _to_absolute(path)
        for root, dirs, files in os.walk(_to_absolute(path)):
            if filter_hidden and any(dirname.startswith(".") for dirname in root.split(os.path.sep)):
                continue
            for name in files + dirs:
                if not (filter_hidden and name.startswith(".")):  # for Posix systems
                    # print("f>", os.path.join(root, name))
                    yield os.path.join(root, name)

    result = find_all(path, skip_hidden)
    if name:
        result |= filter_name(name)
    if file_type:
        result |= filter_filetype(file_type)
    return result


def _to_absolute(path):
    """Returns absolute path of any given path"""
    path = Path(path)
    if path.is_absolute():
        return path
    else:
        return Path(os.path.join(_working_dir,
                                 path)).absolute()  # could simply return Path(path).absolute, but it doesn't work with cd
