import subprocess

from tqdm import tqdm

# https://sourceforge.net/projects/pysh/

_generator_class = type((i for i in []))


class PipeElement:
    pass  # marker class


def generator(gen=None, len_=None):
    if len_ is None:
        return Generator(gen)
    else:
        return KnownLengthGenerator(gen, len_)


class Generator(PipeElement):
    """
    Wrapper for any generator;
    bitwise-or operator creates pipeline or chain of generators
    plus operator concatenates the generators
    """

    def __init__(self, gen=None):
        if "__next__" in dir(gen):
            self._gen = gen
        elif "__iter__" in dir(gen):
            self._gen = iter(gen)
        else:
            self._gen = self.gen()
        self._source = None

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, src):
        if "__next__" in dir(src):
            self._source = src
        elif "__iter__" in dir(src):
            self._source = iter(src)
        else:
            raise TypeError("Source needs to be iterable")

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._gen)

    def __ror__(self, other):
        self.source = other
        return self

    def __or__(self, other):
        if isinstance(other, PipeElement):
            return other.__ror__(self)
        else:
            try:
                gen = other(self)
                assert type(gen) == _generator_class
                return generator(gen).__ror__(self)
            except (TypeError, AssertionError):
                return pipe_from_func(other)().__ror__(self)

    def __add__(self, other):
        return GeneratorConcat(self, other)

    def __radd__(self, other):
        return GeneratorConcat(other, self)


class KnownLengthGenerator(Generator):
    # DONE: cat, cat_list, bz2_cat - cat i bz2_cat kosztowne, więc albo na prośbę użytkownika, albo wg rozmaru pliku w bajtach
    # drains - nie iteruje się po nich
    # grep, comm, diff, uniq - tylko aktualizowane co wywołanie
    # split_sequence dziedziczy (ale dzieli przez długość sekwencji)
    # sort, cut, rev, sed - dziedziczą
    # ls, find - nie da się/bez sensu
    # można spróbować szacować cat i bz2_cat na podstawie rozmiaru w B

    # case 0 - inherit from source
    # case 1 - set one length at the creation
    # case 2 - update length at every generation

    def __init__(self, gen=None, len_=None):
        super().__init__(gen)
        self.__len = len_

    def __len__(self):
        if self.__len == 'inherit':
            return len(self.source)
        else:
            return self.__len


class GeneratorConcat(Generator):
    """Concatenation of generators - generates all data from the first one, then from the second and so on"""

    def __init__(self, *gens):
        assert gens, "Need at least one generator"
        gens = list(gens)
        for i, gen in enumerate(gens):
            if "__next__" not in dir(gen):
                gens[i] = iter(gen)
        self.gens = gens
        self.active = 0

    def __next__(self):
        try:
            while True:
                try:
                    return next(self.gens[self.active])
                except StopIteration:
                    self.active += 1
        except IndexError:
            raise StopIteration()

    def __add__(self, other):
        return GeneratorConcat(self, other)

    def __radd__(self, other):
        return GeneratorConcat(other, self)


def make_pipe(func=None, len_=None, len_update=None):
    """
    Decorator for a function, turning it to generator
    the decorated function is called for every element of source sequence
    len_update: inherit, start, every
    """

    if len_update is None and len_ is not None:
        len_update = 'start'

    def inner(func):
        # @wraps(func)
        class decorator(Generator):

            def __init__(self, *args, **kwargs):
                super().__init__(None)
                self.args = args
                self.kwargs = kwargs
                if len_update == 'start':
                    self.__len = len_(*args, **kwargs)

            def gen(self):
                if self.source is not None:
                    yield from func(self.source, *self.args, **self.kwargs)
                else:
                    if "__iter__" in dir(self.args[0]):
                        self.args = (iter(self.args[0]),) + self.args[1:]
                    yield from func(*self.args, **self.kwargs)

            def __call__(self, source, *args, **kwargs):
                if '__iter__' in dir(source):
                    source = iter(source)
                yield from func(source, *self.args, **self.kwargs)

        if len_update == 'inherit':
            def __len__(self):
                return len(self.source)

        elif len_update is not None:
            def __len__(self):
                return self._decorator__len

        if len_update is not None:
            decorator.__len__ = __len__

        return decorator

    if func is not None:
        return inner(func)
    else:
        return inner


def make_source(func=None, len_=None):
    """Decorator for a function making it available for concatenation and piping"""

    if len_ is None:
        class decorator(Generator):

            def __init__(self, *args, **kwargs):
                super().__init__(None)
                self.args = args
                self.kwargs = kwargs

            def gen(self):
                yield from func(*self.args, **self.kwargs)

        return decorator
    else:
        def inner(func):
            # @wraps(func)
            class decorator(KnownLengthGenerator):

                def __init__(self, *args, **kwargs):
                    super().__init__(None, len_(*args, **kwargs))
                    self.args = args
                    self.kwargs = kwargs

                def gen(self):
                    yield from (elem for elem in func(*self.args, **self.kwargs))

                # __len__ is defined in KnownLengthGenerator

            return decorator

        return inner


def make_drain(f):
    """
    Decorator for a function that is designed to be the last element in pipe
    e.g. echo in the pipe: cat("filename") | grep("pattern") | echo()
    """

    # @wraps(f)
    class drain(PipeElement):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __ror__(self, source):
            return f(source, *self.args, **self.kwargs)

    return drain


def pipe_from_func(func, *args_o, **kwargs_o):
    """
    Turns any given function to pipe, calling it for every element of source sequence
    """

    @make_pipe
    def inner(source, *args, **kwargs):
        for elem in source:
            yield func(elem, *args, *args_o, **kwargs, **kwargs_o)

    return inner


class tqdm_wrapper(tqdm):

    def __iter__(self):
        for elem in super().__iter__():
            self.total = len(self.iterable)
            self.refresh()
            yield elem


@make_source
def split_sequence(seq, part_len):
    if '__iter__' in dir(seq):
        seq = iter(seq)
    empty = False

    def inner():
        try:
            for _ in range(part_len):
                yield next(seq)
        except StopIteration:
            nonlocal empty
            empty = True
            return

    while not empty:
        try:
            yield inner()
        except StopIteration:
            return


class CommandError(Exception):
    pass


def run_command(command, raise_on_error=True):
    """Runs any given shell command and captures its stdout and stderr"""
    result = subprocess.run(command, shell=True, capture_output=True)
    error = result.stderr.decode('utf-8')  # decode bytes to string
    if result.returncode != 0 and raise_on_error:
        raise CommandError('Command returned {} exit code. Stderr:\n{}'.format(result.returncode, error))
    output = result.stdout.decode('utf-8')  # decode bytes to string
    if raise_on_error:
        return output, error
    else:
        return output, error, result.returncode


def _start_application(command):
    """Starts any application. Designed for GUI applications."""
    subprocess.Popen(command, shell=True)
