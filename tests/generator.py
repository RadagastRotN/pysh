import unittest

from pysh import pipe_from_func, cat_list, make_pipe, make_drain


class GeneratorTest(unittest.TestCase):

    def test_pipe_from_func(self):
        repl = pipe_from_func(str.replace)
        self.assertEqual(list(cat_list(['aaa', 'aba', 'bcd']) | repl("a", "X")), ['XXX', 'XbX', 'bcd'])

        to_int = pipe_from_func(int)
        sqr = pipe_from_func(lambda x: x ** 2)
        self.assertEqual(list(cat_list(['1', '2', '13']) | to_int() | sqr()), [1, 4, 169])

    def test_piping(self):
        lower = pipe_from_func(str.lower)

        def lower2(source):
            yield from (x.lower() for x in source)

        res1 = list(cat_list(['A', 'BC', 'DEG']) | lower())
        res2 = list(cat_list(['A', 'BC', 'DEG']) | str.lower)
        res3 = list(cat_list(['A', 'BC', 'DEG']) | lower2)
        self.assertEqual(res1, ['a', 'bc', 'deg'])
        self.assertEqual(res2, ['a', 'bc', 'deg'])
        self.assertEqual(res3, ['a', 'bc', 'deg'])

        @make_pipe
        def filter(source, threshold=0):
            yield from (x for x in source if x > threshold)

        self.assertEqual(list(filter([1, -1, 2, 3], 1)), [2, 3])
        self.assertEqual(list(cat_list([1, -1, 2, 3]) | filter(1)), [2, 3])
        self.assertEqual(list([1, -1, 2, 3] | filter(1)), [2, 3])

    def test_drain(self):
        @make_drain
        def wc(source):
            return sum(1 for _ in source)

        self.assertEqual(cat_list([1, 2, 3, 4]) | wc(), 4)
        self.assertEqual(cat_list(['abc', 2, 'cde', 'x', 10]) | wc(), 5)

    def test_chaining(self):
        res = list([1, 2] + cat_list([3, 4]))
        self.assertEqual(res, [1, 2, 3, 4])
        res = list(cat_list([1, 2]) + cat_list([3, 4]))
        self.assertEqual(res, [1, 2, 3, 4])
        res = list(cat_list([1, 2]) + [3, 4])
        self.assertEqual(res, [1, 2, 3, 4])

    def test_source(self):
        ...  # TODO
