import unittest
from pathlib import Path

from pysh import cat, cat_list, rm, to_bz2, bz2_cat, to_list


class SourcesTest(unittest.TestCase):

    def setUp(self):
        with open("/tmp/pysh_cat_test", "w") as outfile:
            outfile.write("a\nb\ncde\nbde\n\n")

    def tearDown(self) -> None:
        rm("/tmp/pysh_cat_test")

    def test_cat(self):
        content = list(cat("/tmp/pysh_cat_test"))
        self.assertEqual(content, ["a", "b", "cde", "bde", ""])
        gen = cat("/tmp/pysh_cat_test", with_len=True)
        self.assertEqual(len(gen), 5)
        self.assertEqual(list(gen), ["a", "b", "cde", "bde", ""])
        self.assertEqual(len(gen), 5)

    def test_cat_list(self):
        lst = ['a', 'b', 'cde', 'fgh', 'x']
        self.assertEqual(list(cat_list(lst[:])), lst)
        lst = [0, 1, 2, 3, 'a', 'b', 'c', [1, 2, 3]]
        self.assertEqual(list(cat_list(lst[:])), lst)

    def test_bz2_cat(self):
        FNAME = '/tmp/pysh_bz2_test.bz2'
        content = ['a', 'bc', 'def', 'ghi', 'xx']
        cat_list(content) | to_bz2(FNAME)
        self.assertTrue(Path(FNAME).exists())
        result = bz2_cat(FNAME) | to_list()
        self.assertEqual(content, result)
        gen = bz2_cat(FNAME, with_len=True)
        self.assertEqual(len(gen), 5)
        self.assertEqual(content, list(gen))
        content = ['Lorem ipsum dolor sit amet,', 'consectetur adipiscing elit,', 'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.', '×÷±°¾≈']
        cat_list(content) | to_bz2(FNAME)
        self.assertTrue(Path(FNAME).exists())
        result = bz2_cat(FNAME) | to_list()
        self.assertEqual(content, result)
        gen = bz2_cat(FNAME, with_len=True)
        self.assertEqual(len(gen), 4)
        self.assertEqual(content, list(gen))
        rm(FNAME)
