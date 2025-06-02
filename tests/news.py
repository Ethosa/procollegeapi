import unittest

from mounts.news import (
    get_last_college_news,
    get_new_by_id
)


class NewsTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_last_college_news(self):
        news = await get_last_college_news()

        assert len(news) > 0
        print('\nLast actual news:', news[0])
    
    async def test_get_new_by_id(self):
        news = await get_last_college_news()
        last_one = await get_new_by_id(news_id=news[0]['id'])

        print('\nLast one:', last_one)
