import os
import re
import shutil
import sys
from enum import Flag, auto
from operator import itemgetter
from pathlib import Path

import psutil

from .generator import generator, Generator, PipeElement, make_pipe, make_source, make_drain, pipe_from_func

_working_dir = os.path.abspath(os.path.curdir)
_prev_working_dir = _working_dir


class Flags(Flag):
    C = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()
    L = auto()
    N = auto()
    R = auto()
    V = auto()
    W = auto()


NO_FLAGS = Flags.W & Flags.L


def cat(filename, with_len=False):
    """Generates all content from given file line by line, stripping newline characters"""
    if with_len:
        _len = wc(filename, Flags.L)
    else:
        _len = None
    filename = _to_absolute(filename)

    def inner():
        with open(filename) as infile:
            yield from (line[:-1] for line in infile)

    return generator(inner(), len=_len)


class grep(Generator):
    """
    Filters input sequence, retaining only elements matching given expression.
    Params:
    re - expression to be searched for; if it is string it is searched for literally;
        if it is compiled regex it is searched for using the search method
    start_num - if flag N is specified, this argument allows to change the numbering from zero-based (default) to any other
    Flags:
    V - retain only NOT matching elements
    N - prepend numbers
    """

    # i - ignore case
    def __init__(self, pattern, flags=NO_FLAGS, start_num=0):
        super().__init__(None)
        self.re = pattern
        self.start_num = start_num
        self.flags = flags
        if 'search' not in self.re:
            self.re = re.compile(self.re)
        if Flags.I in flags:
            self.re = re.compile(self.re.pattern, self.re.flags | re.IGNORECASE)

    def gen(self):
        match = (lambda x: self.re.search(x)) if Flags.V not in self.flags else (lambda x: not self.re.search(x))
        if Flags.N in self.flags:
            self.source = enumerate(self.source, start=self.start_num)
            _match = match
            match = lambda el: _match(el[1])
        yield from (x for x in self.source if match(x))


@make_pipe
def sed(source, command, src, dest, flags=NO_FLAGS):
    """
    Supports sed s and y command:
    s - substitute the first occurence (or all occurences with G flag) of src string in each line with dest string
    y - substitute any occurence of a char in src string with the corresponding character in dest string
    Flags:
    G - with s command - substitute all (non-overlapping) occurences, instead of only the first one
    """
    if command == 's':
        regex = re.compile(src)
        for line in source:
            yield regex.sub(dest, line, count=0 if Flags.G in flags else 1)
    elif command == 'y':
        assert len(src) == len(dest)
        mapping = dict(zip(src, dest))
        for line in source:
            yield "".join(mapping.get(char, char) for char in line)


class uniq(Generator):
    """
    Filter out repeted elements in input sequence
    Flags:
    C - append the number each element appered in sequence (counting consecutive occurences)
    """

    def __init__(self, flags=NO_FLAGS):
        super().__init__(None)
        self.last = None
        self.flags = flags

    def gen(self):
        if Flags.C in self.flags:
            yield from self._with_count()
        else:
            yield from self._normal()

    def _normal(self):
        last = None
        for elem in self.source:
            if last != elem:
                yield elem
                last = elem

    def _with_count(self):
        count = 1
        first = True
        last = None
        for elem in self.source:
            if elem != last:
                if not first:
                    yield last, count
                    count = 1
                else:
                    first = False
                last = elem
            else:
                count += 1
        yield last, count


class sort(Generator):
    """
    Sort input sequence
    Flags:
    G - sort according to numerical value of (prefix of) the string
    H - as G, but also support suffixes like K for kilo, M for mega etc.
    R - reverse ordering
    """

    def __init__(self, flags=NO_FLAGS):
        super().__init__(None)
        self.content = None
        self.flags = flags

    @staticmethod
    def _general_numeric(elem):
        i = 0 if not elem.startswith("-") else 1
        while i < len(elem) and (elem[i].isdigit() or elem[i].isspace()):
            i += 1
        return int(elem[:i].replace(" ", ""))

    @staticmethod
    def _human_readable(elem: str):
        MULTIPLIERS = {"K": 10 ** 3, "M": 10 ** 6, "G": 10 ** 9, "T": 10 ** 12, "P": 10 ** 15}
        val = sort._general_numeric(elem)
        i = len(str(val))
        while i < len(elem) and (elem[i].isdigit() or elem[
            i].isspace()):  # need to check isdigit in case there are spaces before the number which causes len(str(val)) be less than actual index of the first non-digit character
            i += 1
        if i < len(elem) and elem[i] in MULTIPLIERS and (i + 1 >= len(elem) or elem[i + 1].isspace()):
            val *= MULTIPLIERS[elem[i]]
        return val

    def gen(self):
        if Flags.G in self.flags:
            key = sort._general_numeric
        elif Flags.H in self.flags:
            key = sort._human_readable
        else:
            key = lambda x: x
        self.content = sorted((x for x in self.source), key=key, reverse=(Flags.R in self.flags))
        # the above generator expression avoids calling __len__ where it may not be defined
        yield from self.content


def _wcl(filename):
    with open(filename) as infile:
        return sum(1 for _ in infile)


def _wcc(filename):
    with open(filename) as infile:
        return sum(1 for line in infile for char in line)


def _wcw(filename):
    with open(filename) as infile:
        return sum(1 for line in infile for token in line.split())


def _wc_all(filename):
    chars, words, lines = 0, 0, 0
    with open(filename) as infile:
        for line in infile:
            lines += 1
            chars += len(line)
            words += len(line.split())
    return chars, words, lines


def _wc_all(gen):
    chars, words, lines = 0, 0, 0
    for line in gen:
        lines += 1
        chars += len(line)
        words += len(line.split())
    return [chars, words, lines]


class wc(PipeElement):
    """
    Returns 'word count': number of characters, words and lines
    Counts all characters in input therefor wc(file) gives different output than cat(file) | wc(),
    because the former counts also newline characters which are stripped by cat in latter approach
    Flags:
    C - return character count
    W - return word count
    L - return line count
    No flags specified equal to all flags
    """

    def __init__(self, filename=None, flags=NO_FLAGS):
        if type(filename) is Flags and flags == NO_FLAGS:
            flags = filename
            filename = None
        if flags == NO_FLAGS:
            flags = Flags.C | Flags.W | Flags.L
        self.flags = flags
        self.filename = filename
        if filename:
            with open(filename) as infile:
                self._count(infile)
        else:
            self.res = ()

    def _count(self, gen):
        self.res = _wc_all(gen)
        if Flags.L not in self.flags:
            self.res.pop(2)
        if Flags.W not in self.flags:
            self.res.pop(1)
        if Flags.C not in self.flags:
            self.res.pop(0)
        self.res = tuple(self.res)

    def __ror__(self, other):
        self._count(other)
        return self

    def __getitem__(self, item):
        return self.res[item]

    def __repr__(self):
        return repr(self.res)

    def __iter__(self):
        return iter(self.res)


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


class cut(Generator):
    """
    Cuts each string into parts by given delimiter and returns selected ones;
    parts may be selected both as ranges (e.g. 2-4) or list (e.g. 1,3) or both (e.g. 1-3,5)
    """

    def __init__(self, fields, delimiter=" "):
        super().__init__()
        self.delimiter = delimiter
        if type(fields) is int:
            self.fields = {fields}
        else:
            self.fields = []
            fields = fields.split(",")
            for ind, field in enumerate(fields):
                if "-" in field:
                    field = field.split("-")
                    field = list(range(int(field[0]), int(field[1]) + 1))
                    self.fields += field
                else:
                    self.fields += [int(field)]
            self.fields = sorted(set(self.fields))

    def gen(self):
        for line in self.source:
            yield list(elem for ind, elem in enumerate(line.split(self.delimiter), start=1) if ind in self.fields)


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
            if filter_hidden and any(dirname.startswith(".") for dirname in root.split(os.sep)):
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


class cd:
    """
    Changes the working directory
    cd("-") changes it back to the previous one
    Also works as context manager
    """

    def __init__(self, dir):
        global _working_dir, _prev_working_dir  # yes, I know
        old_working_dir = _working_dir
        self.old_prev_working_dir = _prev_working_dir  # in order to restore it if cd is used as a context manager

        if dir == "-":
            _working_dir, _prev_working_dir = _prev_working_dir, _working_dir
        else:
            _prev_working_dir = _working_dir
            self._previous_dir = _working_dir

            abs_dir = os.path.abspath(os.path.join(_working_dir, dir))
            if abs_dir == dir:
                _working_dir = dir
            else:
                for next_dir in os.path.normpath(dir).split(os.path.sep):
                    if next_dir in ls(only_dirs=True) or next_dir in [os.path.pardir, os.path.curdir]:
                        _working_dir = os.path.join(_working_dir, next_dir)
                    else:
                        raise FileNotFoundError("No such directory {} in {}".format(next_dir, _working_dir))
        if _working_dir != old_working_dir:
            os.chdir(_working_dir)

    def __enter__(self):
        _prev_working_dir = self.old_prev_working_dir
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _working_dir  # yes, I know
        _working_dir = self._previous_dir
        return False


def pwd():
    """Returns current working directory"""
    return _working_dir


@make_drain
def echo(source, out=sys.stdout):
    """Prints the input stream to stdout"""
    for line in source:
        print(line, file=out)


@make_drain
def file_saver(source, filename, mode="w"):
    """
    Saves the input stream to given file
    :param filename: what file to save the stream to
    :param mode: either 'w' or 'a' - the meaning is the same as with open function
    :return: None
    """
    with open(filename, mode) as outfile:
        for line in source:
            outfile.write("{}\n".format(line))


rev = pipe_from_func(lambda s: s[::-1])


def comm(gen1, gen2, suppress=""):
    """
    Takes two sorted streams and outputs one column with elements unique to the forst one,
    second unique to the second one and third common for both; empty columns are filled with Nones
    Args:
        suppress - takes numbers of columns to be omitted from output; e.g. suppress=12 or "12" outputs only the third column
        if only one column is present in the output, the output are just elements, not tuples
    """

    def filter_nones(gen):
        yield from (elem for elem in gen if not (elem is None or type(elem) is tuple and set(elem) == {None}))

    def get_next(gen):
        try:
            return next(gen), False
        except StopIteration:
            return None, True

    if type(suppress) is int:
        suppress = str(suppress)
    assert not (set(suppress) - set("123")), f"Output can consist only of digits 1, 2 and 3 {set(suppress)}"

    get_output = itemgetter(*sorted({0, 1, 2} - {int(col) - 1 for col in suppress}))

    # print(get_output)
    # return

    def inner_gen():
        elem1, gen1_ended = get_next(gen1)
        elem2, gen2_ended = get_next(gen2)
        while True:
            if gen1_ended and gen2_ended:
                break
            elif gen1_ended or elem2 < elem1:
                yield get_output((None, elem2, None))
                elem2, gen2_ended = get_next(gen2)
            elif gen2_ended or elem1 < elem2:
                yield get_output((elem1, None, None))
                elem1, gen1_ended = get_next(gen1)
            else:
                yield get_output((None, None, elem1))
                elem1, gen1_ended = get_next(gen1)
                elem2, gen2_ended = get_next(gen2)

    yield from filter_nones(inner_gen())


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
    if source.is_dir() and Flag.R in flags:
        shutil.copytree(source, dest)
    else:
        shutil.copy(source, dest)


def mv(source, dest):
    """Moves source file or directory to dest"""
    source = _to_absolute(source)
    dest = _to_absolute(dest)
    shutil.move(source, dest)


# shutil.disk_usage(

### helpers

@make_source
def cat_list(l):
    yield from l


@make_drain
def to_list(source):
    return list(elem for elem in source)  # generator expression avoids calling len


def _to_absolute(path):
    """Returns absolute path of any given path"""
    path = Path(path)
    if path.is_absolute():
        return path
    else:
        return Path(os.path.join(_working_dir, path)).absolute()  # could simply return Path(path).absolute, but it doesn't work with cd
