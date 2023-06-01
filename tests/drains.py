import unittest

from pysh import cat_list, to_file, cat, mkdir, rm, Flags, head, to_list, echo


class DrainsTest(unittest.TestCase):
    def setUp(self):
        mkdir("/tmp/pysh_test")

    def tearDown(self) -> None:
        rm("/tmp/pysh_test/", Flags.R)

    def test_file_saver(self):
        cat_list(['a', 'b', 'c', 'd', 'efgh', 'x']) | to_file("/tmp/pysh_test/file_saver_test")
        content = list(cat("/tmp/pysh_test/file_saver_test"))
        self.assertEqual(content, ['a', 'b', 'c', 'd', 'efgh', 'x'])

    def test_to_list(self):
        self.assertEqual([1, 2, 3] | head(2) | to_list(), [1, 2])
        self.assertEqual((i ** 2 for i in range(5)) | to_list(), [0, 1, 4, 9, 16])
        self.assertEqual((ch.lower() for ch in "ABCDEF") | to_list(), list('abcdef'))

    def test_echo(self):
        with open("/tmp/pysh_test/echo_test", "w") as outfile:
            [1, 2, 3] | echo(out=outfile)
        self.assertEqual(cat("/tmp/pysh_test/echo_test") | to_list(), ['1', '2', '3'])
        with open("/tmp/pysh_test/echo_test", "w") as outfile:
            (i ** 2 for i in range(5)) | echo(out=outfile)
        self.assertEqual(cat("/tmp/pysh_test/echo_test") | to_list(), ['0', '1', '4', '9', '16'])
