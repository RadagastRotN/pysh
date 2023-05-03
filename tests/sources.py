import unittest

from pysh import cat, cat_list, rm


class SourcesTest(unittest.TestCase):

    def setUp(self):
        with open("/tmp/pysh_cat_test", "w") as outfile:
            outfile.write("a\nb\ncde\nbde\n\n")

    def tearDown(self) -> None:
        rm("/tmp/pysh_cat_test")

    def test_cat(self):
        content = list(cat("/tmp/pysh_cat_test"))
        self.assertEqual(content, ["a", "b", "cde", "bde", ""])

    def test_cat_list(self):
        lst = ['a', 'b', 'cde', 'fgh', 'x']
        self.assertEqual(list(cat_list(lst[:])), lst)
        lst = [0, 1, 2, 3, 'a', 'b', 'c', [1, 2, 3]]
        self.assertEqual(list(cat_list(lst[:])), lst)

