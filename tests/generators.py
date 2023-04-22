import unittest

from pysh import *
# from pysh.main import cat_list


class PyshTest(unittest.TestCase):

    def setUp(self):
        with open("/tmp/pysh_cat_test", "w") as outfile:
            outfile.write("a\nb\ncde\nbde\n\n")
        mkdir("/tmp/pysh_test/foo/bar/baz")
        mkdir("/tmp/pysh_test/x/y")
        mkdir("/tmp/pysh_test/A/B/C")
        mkdir("/tmp/pysh_test/A/B/D/testy")
        touch("/tmp/pysh_test/foo/bar/baz/xyz.txt")
        touch("/tmp/pysh_test/x/y/foo.txt")
        touch("/tmp/pysh_test/x/y/bar.py")
        touch("/tmp/pysh_test/A/B/test1")
        touch("/tmp/pysh_test/A/B/C/test2")
        touch("/tmp/pysh_test/A/B/D/test3")
        touch("/tmp/pysh_test/A/test4.test")
        cd("/tmp/pysh_test")

    def tearDown(self) -> None:
        rm("/tmp/pysh_test/", Flags.R)
        rm("/tmp/pysh_cat_test")

    def test_cat(self):
        content = list(cat("/tmp/pysh_cat_test"))
        self.assertEqual(content, ["a", "b", "cde", "bde", ""])

    def test_cd_and_pwd(self):
        cd("/tmp/pysh_test")
        self.assertEqual(pwd(), "/tmp/pysh_test")
        cd("x")
        self.assertEqual(pwd(), "/tmp/pysh_test/x")
        cd("-")
        self.assertEqual(pwd(), "/tmp/pysh_test")
        with cd("A/B/C"):
            self.assertEqual(pwd(), "/tmp/pysh_test/A/B/C")
        self.assertEqual(pwd(), "/tmp/pysh_test")
        with self.assertRaises(FileNotFoundError):
            cd("ZZZ")
        self.assertEqual(pwd(), "/tmp/pysh_test")

    def test_ls(self):
        self.assertEqual(set(list(ls(dirname="/tmp/pysh_test/", only_dirs=True))), set("foo x A".split()))
        self.assertEqual(set(list(ls(dirname="/tmp/pysh_test/A/B"))), set("C D test1".split()))
        with cd("/tmp/pysh_test/A/B"):
            self.assertEqual(set(list(ls())), set("C D test1".split()))

    def test_rm(self):
        with open("/tmp/pysh_test/rm_test", "w") as outfile:
            outfile.write("abc\n")
        rm("/tmp/pysh_test/rm_test")
        with self.assertRaises(FileNotFoundError):
            with open("/tmp/rm_test") as infile:
                pass  # no need to do anything

    def test_find(self):
        cd("/tmp/pysh_test")
        # print(list(ls()))
        # print(list(find(".", name="test.*")))
        # print(list(find(".", name=r"test.*")))
        # print(list(ls(dirname="/tmp/pysh_test/foo/bar/baz")))
        # print(list(ls(Flags.R, dirname="/tmp/pysh_test/")))
        results = set(list(find(".", name="test.*")))
        self.assertEqual(results,
                         set("/tmp/pysh_test/A/B/test1 /tmp/pysh_test/A/B/C/test2 /tmp/pysh_test/A/B/D/test3 /tmp/pysh_test/A/test4.test /tmp/pysh_test/A/B/D/testy".split()))
        results = set(list(find(".", name=".*\.test")))
        self.assertEqual(results, set("/tmp/pysh_test/A/test4.test".split()))
        cd("/tmp")
        results = set(list(find("/tmp/pysh_test", name=".*\.py")))
        self.assertEqual(results, set("/tmp/pysh_test/x/y/bar.py".split()))
        results = set(list(find("/tmp/pysh_test", name="B")))
        self.assertEqual(results, set("/tmp/pysh_test/A/B".split()))
        results = set(list(find("pysh_test", name="B", file_type="file")))
        self.assertEqual(results, set())

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

    def test_file_saver(self):
        cat_list("a b c d efgh x".split()) | to_file("/tmp/pysh_test/file_saver_test")
        content = list(cat("/tmp/pysh_test/file_saver_test"))
        self.assertEqual(content, "a b c d efgh x".split())

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

    def test_rev(self):
        self.assertEqual(list(cat_list("abc def aaa".split()) | rev()), "cba fed aaa".split())

    def test_sed(self):
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('y', 'abcd', 'XYZŹ')),
                         "XXXX YXYXY ZŹZŹ".split())
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('s', 'ab', 'X')), "aaaa bXab cdcd".split())
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('s', 'ab', 'X', Flags.G)),
                         "aaaa bXX cdcd".split())
        self.assertEqual(list(cat_list("aaaa babab cdcd".split()) | sed('s', 'a|b', 'X', Flags.G)),
                         "XXXX XXXXX cdcd".split())

    def test_comm(self):
        result = list(comm(cat_list([1, 2, 4]), cat_list([1, 3, 4, 5])))
        self.assertEqual(result, [(None, None, 1), (2, None, None), (None, 3, None), (None, None, 4), (None, 5, None)])
        result = list(comm(cat_list([1, 2, 4]), cat_list([1, 3, 4, 5]), suppress="12"))
        self.assertEqual(result, [1, 4])


if __name__ == '__main__':
    unittest.main()


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
