import re
import re
import unittest
from random import choice
from string import ascii_lowercase

from pysh import cd, pwd, find, ls, rm, mkdir, touch, Flags, cat, to_list, cat_list, to_file, mv
from pysh.file_utils import cp, du


class FileUtilsTest(unittest.TestCase):

    def setUp(self):
        with open("/tmp/pysh_cat_test", "w") as outfile:
            outfile.write("a\nb\ncde\nbde\n\n")
        mkdir("/tmp/pysh_test/foo/bar/baz")
        mkdir("/tmp/pysh_test/x/y")
        mkdir("/tmp/pysh_test/A/B/C")
        mkdir("/tmp/pysh_test/A/B/D/testy")
        touch("/tmp/pysh_test/foo/.hidden1")
        touch("/tmp/pysh_test/foo/.hidden2")
        touch("/tmp/pysh_test/foo/bar/.hidden3")
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

    def test_touch(self):
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/foo/bar/baz/spam'))
        touch('/tmp/pysh_test/foo/bar/baz/spam')
        self.assertEqual(list(cat('/tmp/pysh_test/foo/bar/baz/spam')), [])

    def test_mkdir(self):
        with self.assertRaises(FileNotFoundError):
            list(ls('/tmp/pysh_test/foo/bar/baz/spim'))
        mkdir('/tmp/pysh_test/foo/bar/baz/spim')
        self.assertEqual(ls('/tmp/pysh_test/foo/bar/baz/spim') | to_list(), [])

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
        self.assertEqual(set(ls(Flags.R, "/tmp/pysh_test/A/B")),
                         {'/tmp/pysh_test/A/B/C', '/tmp/pysh_test/A/B/D', '/tmp/pysh_test/A/B/test1',
                          '/tmp/pysh_test/A/B/C/test2', '/tmp/pysh_test/A/B/D/testy', '/tmp/pysh_test/A/B/D/test3'
                          })
        self.assertEqual(set(ls(dirname="/tmp/pysh_test/A/B", only_files=True)), {'test1'})
        with cd("/tmp/pysh_test/A/B"):
            self.assertEqual(set(ls()), {'test1', 'C', 'D'})
        self.assertEqual(set(ls("/tmp/pysh_test/A/B")), {'test1', 'C', 'D'})
        self.assertEqual(set(ls("/tmp/pysh_test/A/B", Flags.R)),
                         {'/tmp/pysh_test/A/B/C', '/tmp/pysh_test/A/B/D', '/tmp/pysh_test/A/B/test1',
                          '/tmp/pysh_test/A/B/C/test2', '/tmp/pysh_test/A/B/D/testy', '/tmp/pysh_test/A/B/D/test3'
                          })

    def test_rm(self):
        with open("/tmp/pysh_test/rm_test", "w") as outfile:
            outfile.write("abc\n")
        rm("/tmp/pysh_test/rm_test")
        with self.assertRaises(FileNotFoundError):
            with open("/tmp/rm_test"):
                pass  # no need to do anything

        mkdir("/tmp/pysh_test/rm_test")
        mkdir("/tmp/pysh_test/rm_test/inner")
        mkdir("/tmp/pysh_test/rm_test/file1")
        mkdir("/tmp/pysh_test/rm_test/inner/file2")
        self.assertTrue('/tmp/pysh_test/rm_test/inner' in set(ls('/tmp/pysh_test', Flags.R)))
        self.assertTrue('/tmp/pysh_test/rm_test/inner/file2' in set(ls('/tmp/pysh_test', Flags.R)))

        rm('/tmp/pysh_test/rm_test', Flags.R)
        with self.assertRaises(FileNotFoundError):
            open("/tmp/rm_test/file1")
        self.assertFalse('/tmp/pysh_test/rm_test/inner' in set(ls('/tmp/pysh_test', Flags.R)))
        self.assertFalse('/tmp/pysh_test/rm_test/inner/file2' in set(ls('/tmp/pysh_test', Flags.R)))

        with self.assertRaises(FileNotFoundError):
            rm('/tmp/pysh_test/not_existing_file')
        rm('/tmp/pysh_test/not_existing_file', Flags.F)

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
        results = set(find("pysh_test", name="B", file_type="dir"))
        self.assertEqual(results, {'/tmp/pysh_test/A/B'})
        results = set(find("pysh_test/foo/", file_type="file"))
        self.assertEqual(results, {'/tmp/pysh_test/foo/.hidden1', '/tmp/pysh_test/foo/.hidden2',
                                   '/tmp/pysh_test/foo/bar/.hidden3', '/tmp/pysh_test/foo/bar/baz/xyz.txt'})
        results = set(find("pysh_test/foo/", file_type="dir"))
        self.assertEqual(results, {'/tmp/pysh_test/foo/bar', '/tmp/pysh_test/foo/bar/baz'})
        results = set(find("pysh_test/foo/", file_type="file", skip_hidden=True))
        self.assertEqual(results, {'/tmp/pysh_test/foo/bar/baz/xyz.txt'})

    def test_mv(self):
        original = ['a', 'b', 'c', 'd']
        cat_list(original) | to_file('/tmp/pysh_test/mv_test')
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/test_mv'))
        mv('/tmp/pysh_test/mv_test', '/tmp/pysh_test/test_mv')
        self.assertEqual(list(cat('/tmp/pysh_test/test_mv')), original)
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/mv_test'))

        original = ['a', 'b', 'c', 'd']
        cat_list(original) | to_file('/tmp/pysh_test/mv_test')
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/A/B/D/test_mv'))
        with cd('/tmp/pysh_test'):
            mv('mv_test', 'A/B/D/test_mv')
        self.assertEqual(list(cat('/tmp/pysh_test/A/B/D/test_mv')), original)
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/mv_test'))

    def test_cp(self):
        original = ['a', 'b', 'c', 'd']
        cat_list(original) | to_file('/tmp/pysh_test/cp_test')
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/test_cp'))
        cp('/tmp/pysh_test/cp_test', '/tmp/pysh_test/test_cp')
        self.assertEqual(list(cat('/tmp/pysh_test/test_cp')), original)
        self.assertEqual(list(cat('/tmp/pysh_test/cp_test')), original)

        original = ['a', 'b', 'c', 'd']
        cat_list(original) | to_file('/tmp/pysh_test/cp_test')
        with self.assertRaises(FileNotFoundError):
            list(cat('/tmp/pysh_test/A/B/D/test_cp'))
        with cd('/tmp/pysh_test'):
            cp('cp_test', 'A/B/D/test_cp')
        self.assertEqual(list(cat('/tmp/pysh_test/A/B/D/test_cp')), original)
        self.assertEqual(list(cat('/tmp/pysh_test/cp_test')), original)

    def test_mkdir(self):
        with self.assertRaises(FileNotFoundError):
            list(ls('/tmp/pysh_test/mkdir_test'))
        mkdir('/tmp/pysh_test/mkdir_test')
        self.assertEqual(list(ls('/tmp/pysh_test/mkdir_test')), [])

    def test_du(self):
        cat_list(["abecadło", "Ala ma kota", 'xyz' * 100]) | to_file('/tmp/pysh_test/du_test')
        self.assertEqual(du('/tmp/pysh_test/du_test'), 323)
        cat_list([''.join([choice(ascii_lowercase) for _ in range(9876)])]) | to_file('/tmp/pysh_test/du_test')
        self.assertEqual(du('/tmp/pysh_test/du_test'), 9877)

# TODO: df?
