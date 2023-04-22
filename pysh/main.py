import re
from enum import Flag, auto
from operator import itemgetter

from .generator import Generator, PipeElement, make_pipe, pipe_from_func


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

rev = pipe_from_func(lambda s: s[::-1])


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
