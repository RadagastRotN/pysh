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

    def test_find(self):  # TODO: file_type other than "file"
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
        results = set(find("pysh_test/foo/", file_type="file"))
        self.assertEqual(results, {'/tmp/pysh_test/foo/.hidden1', '/tmp/pysh_test/foo/.hidden2', '/tmp/pysh_test/foo/bar/.hidden3','/tmp/pysh_test/foo/bar/baz/xyz.txt'})
        results = set(find("pysh_test/foo/", file_type="file", skip_hidden=True))
        self.assertEqual(results, {'/tmp/pysh_test/foo/bar/baz/xyz.txt'})


# TODO: mv, cp, touch, mkdir, du, df?
