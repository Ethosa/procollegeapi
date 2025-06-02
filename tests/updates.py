import unittest

from mounts.updates import (
    check_for_updates
)


class UpdatesTest(unittest.IsolatedAsyncioTestCase):
    async def test_check_for_updates(self):
        last_version = await check_for_updates()

        assert 'version' in last_version
        print('\nLast app version:', last_version['version'])
