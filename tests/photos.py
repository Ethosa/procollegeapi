import unittest

from mounts.photos import (
    get_all_albums,
    get_album_by_id
)


class PhotosTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_all_albums(self):
        albums = await get_all_albums()

        assert len(albums) > 0
        print('\nLast album:', albums[0])
    
    async def test_get_album_by_id(self):
        albums = await get_all_albums()
        last_one = await get_album_by_id(album_id=albums[0]['id'])

        print('\nLast one album:', last_one)
