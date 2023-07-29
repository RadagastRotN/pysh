import bz2
import sys

from .generator import make_drain


@make_drain
def to_list(source):
    return list(source)


@make_drain
def echo(source, out=sys.stdout):
    """Prints the input stream to stdout"""
    for line in source:
        print(line, file=out)


@make_drain
def to_file(source, filename, mode="w"):
    """
    Saves the input stream to given file
    :param filename: what file to save the stream to
    :param mode: either 'w' or 'a' - the meaning is the same as with open function
    :return: None
    """
    with open(filename, mode) as outfile:
        for line in source:
            outfile.write("{}\n".format(line))


@make_drain
def to_bz2(source, filename, mode='wt'):
    if 't' in mode:
        source = (line + '\n' for line in source)
    with bz2.open(filename, mode) as outfile:
        for line in source:
            outfile.write(line)
