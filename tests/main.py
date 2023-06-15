import re
import unittest

from pysh import *


class PyshTest(unittest.TestCase):

    def setUp(self):
        with open("/tmp/pysh_cat_test", "w") as outfile:
            outfile.write("a\nb\ncde\nbde\n\n")
        mkdir("/tmp/pysh_test")
        cd("/tmp/pysh_test")

    def tearDown(self) -> None:
        rm("/tmp/pysh_test/", Flags.R)
        rm("/tmp/pysh_cat_test")

    def test_rev(self):
        self.assertEqual(list(cat_list(['abc', 'def', 'aaa']) | rev()), ['cba', 'fed', 'aaa'])

    def test_grep(self):
        result = list(cat("/tmp/pysh_cat_test") | grep("b"))
        self.assertEqual(result, ["b", "bde"])
        result = list(cat("/tmp/pysh_cat_test") | grep("de"))
        self.assertEqual(result, ["cde", "bde"])
        result = list(cat("/tmp/pysh_cat_test") | grep("ce"))
        self.assertEqual(result, [])
        result = list(cat_list(['abc', 'cde', 'bcd', 'bof', 'xxx']) | grep("b", Flags.N))
        self.assertEqual(result, [(0, "abc"), (2, "bcd"), (3, "bof")])
        result = list(cat_list(['abc', 'cde', 'bCd', 'bof', 'xxx', 'BCD']) | grep("Bc", Flags.N | Flags.I))
        self.assertEqual(result, [(0, "abc"), (2, "bCd"), (5, "BCD")])
        result = list(cat_list(['abc', 'bcd', 'deef']) | grep(re.compile(r"[ea]+"), Flags.V))
        self.assertEqual(result, ["bcd"])
        result = list(cat_list(['abc', 'cde', 'bCd', 'bof', 'xxx', 'BCD']) | grep("Bc", Flags.N | Flags.I, start_num=1))
        self.assertEqual(result, [(1, "abc"), (3, "bCd"), (6, "BCD")])

    def test_uniq(self):
        result = list(cat_list(['a', 'a', 'b', 'b', 'b', 'c', 'd', 'ee', 'ee', 'ee', 'f', 'ff', 'a']) | uniq())
        self.assertEqual(result, ['a', 'b', 'c', 'd', 'ee', 'f', 'ff', 'a'])
        result = list(cat_list(['a', 'a', 'b', 'b', 'b', 'c', 'd', 'ee', 'ee', 'ee', 'f', 'ff', 'a']) | uniq(Flags.C))
        self.assertEqual(result, [('a', 2), ('b', 3), ('c', 1), ('d', 1), ('ee', 3), ('f', 1), ('ff', 1), ('a', 1)])

    def test_sort(self):
        result = list(['a', 'x', 'c', 'b', 'cd', 'aa'] | sort())
        self.assertEqual(result, ['a', 'aa', 'b', 'c', 'cd', 'x'])
        result = list(['a', 'x', 'c', 'b', 'cd', 'aa'] | sort(Flags.R))
        self.assertEqual(result, ['x', 'cd', 'c', 'b', 'aa', 'a'])
        result = list(['10 a', '4 x', '3 c', ' 5 b', '6 cd', '2 aa'] | sort(Flags.G))
        self.assertEqual(result, ['2 aa', '3 c', '4 x', ' 5 b', '6 cd', '10 a'])

        result = list(['10M a', '4K x', '3 M c', ' 5 K b', '6 cd', '2G aa'] | sort(Flags.G))
        self.assertEqual(result, ['2G aa', '3 M c', '4K x', ' 5 K b', '6 cd', '10M a'])
        result = list(['10M a', '4K x', '3 M c', ' 5 K b', '6 cd', '2G aa'] | sort(Flags.H))
        self.assertEqual(result, ['6 cd', '4K x', ' 5 K b', '3 M c', '10M a', '2G aa'])
        result = list(['10M a', '4K x', '3 M c', ' 5 K b', '6 cd', '2G aa'] | sort(Flags.H | Flags.R))
        self.assertEqual(result, ['2G aa', '10M a', '3 M c', ' 5 K b', '4K x', '6 cd'])
        result = list(['3 a', '2 c', ' 1b'] | sort(Flags.G))
        self.assertEqual(result, [' 1b', '2 c', '3 a'])
        result = list(['3 K', ' 1G', '2 M'] | sort(Flags.H))
        self.assertEqual(result, ['3 K', '2 M', ' 1G'])

    def test_sed(self):
        self.assertEqual(list(cat_list(['aaaa', 'babab', 'cdcd']) | sed('y', 'abcd', 'XYZŹ')),
                         ['XXXX', 'YXYXY', 'ZŹZŹ'])
        self.assertEqual(list(cat_list(['aaaa', 'babab', 'cdcd']) | sed('s', 'ab', 'X')), ['aaaa', 'bXab', 'cdcd'])
        self.assertEqual(list(cat_list(['aaaa', 'babab', 'cdcd']) | sed('s', 'ab', 'X', Flags.G)),
                         ['aaaa', 'bXX', 'cdcd'])
        self.assertEqual(list(cat_list(['aaaa', 'babab', 'cdcd']) | sed('s', 'a|b', 'X', Flags.G)),
                         ['XXXX', 'XXXXX', 'cdcd'])

    def test_cut(self):
        self.assertEqual(list(cat_list(['a|b', 'c|d']) | cut(delimiter="|", fields=2)), [["b"], ["d"]])
        self.assertEqual(
            list(cat_list(['a.b.c.d.e', 'x.y.z.ź.ż', 'i.j.k.l.m']) | cut(delimiter=".", fields="1,3-4")),
            [["a", "c", "d"], ["x", "z", "ź"], ["i", "k", "l"]])
        with self.assertRaises(ValueError):
            list(cat_list(['a b c', 'd e f', 'g h']) | cut("2,3"))

        result = list(cat_list(['a b c', 'd e f', 'g h']) | cut('2,3', skip_errors=True))
        self.assertEqual(result, [['b', 'c'], ['e', 'f'], ['h']])

    def test_wc(self):
        cat_list(['a', 'b', 'c', 'd', 'efgh\t1', 'x']) | to_file("/tmp/pysh_test/wc_test")
        self.assertEqual(tuple(cat_list(['a', 'b', 'c', 'd', 'efgh\t1', 'x']) | wc()), (11, 7, 6))
        self.assertEqual(tuple(wc("/tmp/pysh_test/wc_test")), (17, 7, 6))
        self.assertEqual(wc("/tmp/pysh_test/wc_test", Flags.L), (6,))
        self.assertEqual(wc("/tmp/pysh_test/wc_test", Flags.W | Flags.L), (7, 6))
        self.assertEqual(tuple(cat("/tmp/pysh_test/wc_test") | wc()), (11, 7, 6))

    def test_comm(self):
        result = list(comm(cat_list([1, 2, 4]), cat_list([1, 3, 4, 5])))
        self.assertEqual(result, [(None, None, 1), (2, None, None), (None, 3, None), (None, None, 4), (None, 5, None)])
        result = list(comm(cat_list([1, 2, 4]), cat_list([1, 3, 4, 5]), suppress="12"))
        self.assertEqual(result, [1, 4])
        with self.assertRaises(ValueError):
            list(comm(cat_list([1, 4, 2]), cat_list([1, 2, 4]), suppress="12"))

    def test_diff(self):
        self.assertEqual(diff("abc", "abcd", start_num=1), ['3a4', '> d'])
        self.assertEqual(diff("abcd", "abc", start_num=1), ['4d3', '< d'])
        self.assertEqual(diff("abxyc", "abc", start_num=1), ['3,4d2', '< x', '< y'])
        self.assertEqual(diff("axbc", "abyc", start_num=1), ['2d1', '< x', '3a3', '> y'])
        self.assertEqual(diff("axbc", "ayzbc", start_num=1), ['2c2,3', '< x', '> y', '> z'])
        self.assertEqual(diff(['aa', 'bb', 'cde'], ['bb', 'cdf'], start_num=1),
                         ['1d0', '< aa', '3c2', '< cde', '> cdf'])
        self.assertEqual(diff(['bb', 'cdf'], ['aa', 'bb', 'cde'], start_num=1),
                         ['0a1', '> aa', '2c3', '< cdf', '> cde'])
        self.assertEqual(diff("abc", "abcd"), ['2a3', '> d'])
        self.assertEqual(diff("axbc", "abyc"), ['1d0', '< x', '2a2', '> y'])

    def test_head(self):
        self.assertEqual(list(range(100) | head()), list(range(10)))
        self.assertEqual(list(range(100) | head(-10)), list(range(90)))
        self.assertEqual(list(range(100) | head(5)), list(range(5)))
        self.assertEqual(list(range(100) | head(-5)), list(range(95)))

    def test_tail(self):
        self.assertEqual(list(range(100) | tail()), list(range(90, 100)))
        self.assertEqual(list(range(100) | tail(-10)), list(range(10, 100)))
        self.assertEqual(list(range(100) | tail(5)), list(range(95, 100)))
        self.assertEqual(list(range(100) | tail(-5)), list(range(5, 100)))
