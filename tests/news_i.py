import unittest
from random import choice

from mounts.news import get_last_college_news
from mounts.photos import get_all_albums
from mounts.media import proxy_file_get


class NewsITest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.news_last_one = (await get_last_college_news())[0]
        self.album_last_one = (await get_all_albums())[0]

    async def test_proxy_files(self):
        if self.news_last_one['preview']:
          print("News preview:", self.news_last_one['preview'])
          assert await proxy_file_get(self.news_last_one['preview']) is not None
        if self.album_last_one['preview']:
          print("Album preview:", self.album_last_one['preview'])
          assert await proxy_file_get(self.album_last_one['preview']) is not None
    