import unittest

from mounts.branches import (
    get_all_branches
)


class BranchesTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_all_branches(self):
        branches = await get_all_branches()

        assert len(branches) == 3
