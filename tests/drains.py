import unittest

from pysh import cat_list, to_file, cat, mkdir, cd, rm, Flags


class DrainsTest(unittest.TestCase):
    def setUp(self):
        mkdir("/tmp/pysh_test")

    def tearDown(self) -> None:
        rm("/tmp/pysh_test/", Flags.R)

    def test_file_saver(self):
        cat_list(['a', 'b', 'c', 'd', 'efgh', 'x']) | to_file("/tmp/pysh_test/file_saver_test")
        content = list(cat("/tmp/pysh_test/file_saver_test"))
        self.assertEqual(content, ['a', 'b', 'c', 'd', 'efgh', 'x'])

# TODO: to_list i echo (echo przyjmuje parametr, do jakiego pliku ma wysyłać)

