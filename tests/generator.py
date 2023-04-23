import unittest

from pysh import pipe_from_func, cat_list


class GeneratorTest(unittest.TestCase):

    def test_pipe_from_func(self):
        repl = pipe_from_func(str.replace)
        self.assertEqual(list(cat_list("aaa aba bcd".split()) | repl("a", "X")), "XXX XbX bcd".split())

        to_int = pipe_from_func(int)
        sqr = pipe_from_func(lambda x: x ** 2)
        self.assertEqual(list(cat_list("1 2 13".split()) | to_int() | sqr()), [1, 4, 169])

    def test_piping(self):
        lower = pipe_from_func(str.lower)

        def lower2(source):
            yield from (x.lower() for x in source)

        res1 = list(cat_list("A BC DEG".split()) | lower())
        res2 = list(cat_list("A BC DEG".split()) | str.lower)
        res3 = list(cat_list("A BC DEG".split()) | lower2)
        self.assertEqual(res1, "a bc deg".split())
        self.assertEqual(res2, "a bc deg".split())
        self.assertEqual(res3, "a bc deg".split())

