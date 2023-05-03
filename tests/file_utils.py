import re
import unittest

from pysh import cd, pwd, find, ls, rm, mkdir, touch, Flags


class FileUtilsTest(unittest.TestCase):

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
        with self.assertRaises(FileNotFoundError):
            cd("/tmp/pysh_test/nonexistent_directory")
        with self.assertRaises(FileNotFoundError):
            cd("/tmp /pysh_test")

    def test_ls(self):
        self.assertEqual(set(ls(dirname="/tmp/pysh_test/", only_dirs=True)), {'A', 'foo', 'x'})
        self.assertEqual(set(ls(dirname="/tmp/pysh_test/A/B")), {'test1', 'C', 'D'})
        with cd("/tmp/pysh_test/A/B"):
            self.assertEqual(set(ls()), {'test1', 'C', 'D'})

    def test_rm(self):
        with open("/tmp/pysh_test/rm_test", "w") as outfile:
            outfile.write("abc\n")
        rm("/tmp/pysh_test/rm_test")
        with self.assertRaises(FileNotFoundError):
            with open("/tmp/rm_test"):
                pass  # no need to do anything

    def test_find(self):
        cd("/tmp/pysh_test")
        results = set(find(".", name="test.*"))
        self.assertEqual(results,
                         {'/tmp/pysh_test/A/B/test1', '/tmp/pysh_test/A/B/C/test2', '/tmp/pysh_test/A/test4.test',
                          '/tmp/pysh_test/A/B/D/testy', '/tmp/pysh_test/A/B/D/test3'})
        results = set(find(".", name=".*\.test"))
        self.assertEqual(results, {"/tmp/pysh_test/A/test4.test"})
        cd("/tmp")
        results = set(find("/tmp/pysh_test", name=r".*\.py"))
        self.assertEqual(results, {'/tmp/pysh_test/x/y/bar.py'})
        results = set(find("/tmp/pysh_test", name=re.compile(r".*\.py")))
        self.assertEqual(results, {'/tmp/pysh_test/x/y/bar.py'})
        results = set(find("/tmp/pysh_test", name="B"))
        self.assertEqual(results, {'/tmp/pysh_test/A/B'})
        results = set(find("pysh_test", name="B", file_type="file"))
        self.assertEqual(results, set())
        # test skip_hidden

# TODO: mv, touch, mkdir
