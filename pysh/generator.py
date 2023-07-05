import subprocess

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

    def __init__(self, gen=None, len=None):
        super().__init__(gen)
        self.__len = len

    def __len__(self):
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


def make_pipe(len_):
    """
    Decorator for a function, turning it to generator
    the decorated function is called for every element of source sequence
    """

    def inner(func):
        # @wraps(func)
        class decorator(Generator):

            def __init__(self, *args, **kwargs):
                super().__init__(None)
                self.args = args
                self.kwargs = kwargs

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

        return decorator

    if "__call__" in dir(len_):
        return inner(len_)
    else:
        return inner


def make_source(len_):
    """Decorator for a function making it available for concatenation and piping"""

    if "__call__" in dir(len_):
        def inner(func):
            # @wraps(func)
            class decorator(Generator):

                def __init__(self, *args, **kwargs):
                    super().__init__(None)
                    self.args = args
                    self.kwargs = kwargs

                def gen(self):
                    yield from func(*self.args, **self.kwargs)

            return decorator

        return inner(len_)
    else:
        def inner(func):
            # @wraps(func)
            class decorator(KnownLengthGenerator):

                def __init__(self, *args, **kwargs):
                    super().__init__(None, len_)
                    self.args = args
                    self.kwargs = kwargs

                def gen(self):
                    yield from (elem for elem in func(*self.args, **self.kwargs))

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


def _run_command(command):
    """Runs any given shell command and captures its stdout and stderr"""
    result = subprocess.run(command, shell=True, capture_output=True)
    output = result.stdout.decode('utf-8')  # decode bytes to string
    error = result.stderr.decode('utf-8')  # decode bytes to string
    return output, error


def _start_application(command):
    """Starts any application. Designed for GUI applications."""
    subprocess.Popen(command, shell=True)
