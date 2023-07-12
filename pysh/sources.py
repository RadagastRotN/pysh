import bz2

from pysh import wc, Flags
from pysh.file_utils import _to_absolute
from pysh.generator import make_source, generator


def cat(filename, with_len=False):
    """Generates all content from given file line by line, stripping newline characters"""
    if with_len:
        len_ = wc(filename, Flags.L)[0]
    else:
        len_ = None
    filename = _to_absolute(filename)

    def inner():
        with open(filename) as infile:
            yield from (line[:-1] for line in infile)

    return generator(inner(), len_=len_)


@make_source(len_=lambda lst: len(lst))
def cat_list(lst):
    yield from lst


def bz2_cat(filename, with_len=False):
    if with_len:
        with bz2.open(filename, 'rt') as infile:
            len_ = max(i for i, _ in enumerate(infile)) + 1
    else:
        len_ = None
    filename = _to_absolute(filename)

    def inner():
        with bz2.open(filename, 'rt') as infile:
            for line in infile:
                yield line[:-1]

    return generator(inner(), len_=len_)
