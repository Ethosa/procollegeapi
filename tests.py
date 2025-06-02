import unittest

from tests.timetable import TimetableTest
from tests.teachers import TeachersTest
from tests.news import NewsTest
from tests.photos import PhotosTest
from tests.contacts import ContactsTest
from tests.updates import UpdatesTest
from tests.branches import BranchesTest
from tests.media import MediaTest


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TimetableTest))
    suite.addTests(loader.loadTestsFromTestCase(TeachersTest))
    suite.addTests(loader.loadTestsFromTestCase(NewsTest))
    suite.addTests(loader.loadTestsFromTestCase(PhotosTest))
    suite.addTests(loader.loadTestsFromTestCase(ContactsTest))
    suite.addTests(loader.loadTestsFromTestCase(BranchesTest))
    suite.addTests(loader.loadTestsFromTestCase(UpdatesTest))
    suite.addTests(loader.loadTestsFromTestCase(MediaTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
