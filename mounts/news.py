from fastapi import FastAPI
from aiohttp import ClientSession
from markdownify import markdownify
from bs4 import BeautifulSoup

from constants import MAIN_WEBSITE
from utils import beautify_src


news_app = FastAPI()


@news_app.get('/')
async def get_last_college_news(md: bool = False):
    session = ClientSession()
    result = []
    async with session.get(MAIN_WEBSITE) as resp:
        page_data = BeautifulSoup(await resp.text())
        for item in page_data.find_all('table', {'class': 'newsitem'}):
            is_announce = item.find('td', {'class': 'date'})
            if is_announce:
                preview_image = item.find('div', {'class': 'annonce'}).find('img')
                data = {
                    'day': item.find('td', {'class': 'date'}).find('span', {'class': 'day'}).text.strip(),
                    'month': item.find('td', {'class': 'date'}).find('span', {'class': 'month'}).text.strip(),
                    'title': item.find('a', {'class': 'title'}).text.strip(),
                    'description': item.find('div', {'class': 'annonce'}).text.strip(),
                    'preview': beautify_src(preview_image.get('src'), MAIN_WEBSITE) if preview_image else '',
                    'type': 'announce'
                }
            else:
                preview_image = item.find('td', {'class': 'annonce'}).find('img')
                data = {
                    'date': item.find('span', {'class': 'datetime'}).text.strip(),
                    'title': item.find('a', {'class': 'greentitle'}).text.strip(),
                    'description': item.find('td', {'class': 'annonce'}).text.replace('[подробнее]', '').strip(),
                    'preview': beautify_src(preview_image.get('src'), MAIN_WEBSITE) if preview_image else '',
                    'type': 'news'
                }
            result.append(data)
    await session.close()
    return result
