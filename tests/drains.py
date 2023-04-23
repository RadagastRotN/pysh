import unittest

from pysh import cat_list, to_file, cat, mkdir, cd, rm, Flags


class DrainsTest(unittest.TestCase):
    def setUp(self):
        with open("/tmp/pysh_cat_test", "w") as outfile:
            outfile.write("a\nb\ncde\nbde\n\n")
        mkdir("/tmp/pysh_test")
        cd("/tmp/pysh_test")

    def tearDown(self) -> None:
        rm("/tmp/pysh_test/", Flags.R)
        rm("/tmp/pysh_cat_test")

    def test_file_saver(self):
        cat_list("a b c d efgh x".split()) | to_file("/tmp/pysh_test/file_saver_test")
        content = list(cat("/tmp/pysh_test/file_saver_test"))
        self.assertEqual(content, "a b c d efgh x".split())

# brakuje to_list i echo (echo przyjmuje parametr, do jakiego pliku ma wysyłać)
