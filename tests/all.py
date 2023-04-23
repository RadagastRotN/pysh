import unittest

from .drains import DrainsTest
from .file_utils import FileUtilsTest
from .generator import GeneratorTest
from .main import PyshTest
from .sources import SourcesTest

ALL_TEST = [SourcesTest, DrainsTest, FileUtilsTest, GeneratorTest, PyshTest]  # to stop PyCharm from removing imports

if __name__ == '__main__':
    unittest.main()

