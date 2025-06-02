import unittest

from mounts.contacts import (
    get_contacts
)


class ContactsTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_contacts(self):
        contacts = await get_contacts()

        assert len(contacts) > 0
        print('\nLast contact:', contacts[0])
