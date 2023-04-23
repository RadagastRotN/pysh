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
        self.assertEqual(list(cat_list("abc def aaa".split()) | rev()), "cba fed aaa".split())

    def test_grep(self):
        result = list(cat("/tmp/pysh_cat_test") | grep("b"))
        self.assertEqual(result, ["b", "bde"])
        result = list(cat("/tmp/pysh_cat_test") | grep("de"))
        self.assertEqual(result, ["cde", "bde"])
        result = list(cat("/tmp/pysh_cat_test") | grep("ce"))
        self.assertEqual(result, [])
        result = list(cat_list("abc cde bcd bof xxx".split()) | grep("b", Flags.N))
        self.assertEqual(result, [(0, "abc"), (2, "bcd"), (3, "bof")])
        result = list(cat_list("abc cde bCd bof xxx BCD".split()) | grep("Bc", Flags.N | Flags.I))
        self.assertEqual(result, [(0, "abc"), (2, "bCd"), (5, "BCD")])

    def test_uniq(self):
        result = list(cat_list("a a b b b c d ee ee ee f ff a".split()) | uniq())
        self.assertEqual(result, "a b c d ee f ff a".split())
        result = list(cat_list("a a b b b c d ee ee ee f ff a".split()) | uniq(Flags.C))
        self.assertEqual(result, list(zip("a b c d ee f ff a".split(), (2, 3, 1, 1, 3, 1, 1, 1))))

    def test_sort(self):
        result = list(cat_list("a x c b cd aa".split()) | sort())
        self.assertEqual(result, "a aa b c cd x".split())

    def test_sed(self):
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('y', 'abcd', 'XYZŹ')),
                         "XXXX YXYXY ZŹZŹ".split())
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('s', 'ab', 'X')), "aaaa bXab cdcd".split())
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('s', 'ab', 'X', Flags.G)),
                         "aaaa bXX cdcd".split())
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('s', 'a|b', 'X', Flags.G)),
                         "XXXX XXXXX cdcd".split())

    def test_cut(self):
        self.assertEqual(list(cat_list("a|b c|d".split()) | cut(delimiter="|", fields=2)), [["b"], ["d"]])
        self.assertEqual(
            list(cat_list("a.b.c.d.e x.y.z.ź.ż i.j.k.l.m".split()) | cut(delimiter=".", fields="1,3-4")),
            [["a", "c", "d"], ["x", "z", "ź"], ["i", "k", "l"]])

    def test_wc(self):
        cat_list("a b c d efgh\t1 x".split(" ")) | to_file("/tmp/pysh_test/wc_test")
        self.assertEqual(tuple(cat_list("a b c d efgh\t1 x".split(" ")) | wc()), (11, 7, 6))
        self.assertEqual(tuple(wc("/tmp/pysh_test/wc_test")), (17, 7, 6))
        self.assertEqual(tuple(cat("/tmp/pysh_test/wc_test") | wc()), (11, 7, 6))



    def test_comm(self):
        result = list(comm(cat_list([1, 2, 4]), cat_list([1, 3, 4, 5])))
        self.assertEqual(result, [(None, None, 1), (2, None, None), (None, 3, None), (None, None, 4), (None, 5, None)])
        result = list(comm(cat_list([1, 2, 4]), cat_list([1, 3, 4, 5]), suppress="12"))
        self.assertEqual(result, [1, 4])





def foo():
    print(*ls("/home/radagast/Rejs/", Flags.R))

    print(_working_dir)
    cd("Projekty")
    print(_working_dir)
    cd("Pysh")
    print(_working_dir)
    cd("-")
    print(_working_dir)
    cd("-")
    print(_working_dir)
    cd("-")
    print(_working_dir)
    print(*ls())

    gen = cat_list("abc bcd deef".split()) | grep(regex.compile(r"[ea]+"), Flags.V)
    for x in gen:
        print(x)

    # cat("memorado")
    cd("Rozwój")
    cat("memorado") | echo()
    cd("..")
    cat("memorado")

    print(pwd())
    with cd("Rozwój"):
        print(pwd())
        with open("memorado") as infile:
            print(infile.read())
    print(pwd())

    # for fname in find("/home/radagast/Projekty/Pysh/", name="py", skip_hidden=True):
    #     print(fname)
