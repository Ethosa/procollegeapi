from fastapi import FastAPI
from aiohttp import ClientSession
from markdownify import markdownify
from bs4 import BeautifulSoup

from constants import MAIN_WEBSITE, MAIN_WEBSITE_ALL_NEWS
from utils import beautify_src, clean_styles


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
                    'id': int(item.find('a', {'class': 'title'}).get('href').split('nid=')[1]),
                    'date': item.find('td', {'class': 'date'}).text.strip().replace('\n', ' '),
                    'title': item.find('a', {'class': 'title'}).text.strip(),
                    'description': item.find('div', {'class': 'annonce'}).text.strip(),
                    'preview': beautify_src(preview_image.get('src'), MAIN_WEBSITE) if preview_image else '',
                    'type': 'announce'
                }
            else:
                preview_image = item.find('td', {'class': 'annonce'}).find('img')
                data = {
                    'id': int(item.find('a', {'class': 'greentitle'}).get('href').split('nid=')[1]),
                    'date': item.find('span', {'class': 'datetime'}).text.strip(),
                    'title': item.find('a', {'class': 'greentitle'}).text.strip(),
                    'description': item.find('td', {'class': 'annonce'}).text.replace('[подробнее]', '').strip(),
                    'preview': beautify_src(preview_image.get('src'), MAIN_WEBSITE) if preview_image else '',
                    'type': 'news'
                }
            if md:
                data['description'] = markdownify(data['description'])
            result.append(data)
    await session.close()
    return result


@news_app.get('/full')
async def get_all_news(page: int = 1, md: bool = False):
    session = ClientSession()
    result = []

    async with session.get(MAIN_WEBSITE_ALL_NEWS + f'?p_cur={page-1}') as resp:
        page_data = BeautifulSoup(await resp.text())

        for item in page_data.find_all('div', {'class': 'newslist'}):
            preview_image = item.find('img')
            description = item.find('div', {'style': 'text-align: justify;'})
            if description is None:
                description = item.find('span', {'style': 'text-align: justify;'})
            data = {
                'id': int(item.find('a', {'class': 'title'}).get('href').split('nid=')[1]),
                'date': item.find('span', {'class': 'date'}).text.strip().replace('\n', ' '),
                'title': item.find('a', {'class': 'title'}).text.strip(),
                'description': description.text.strip().replace('[подробнее]', '') if description is not None else '',
                'preview': beautify_src(preview_image.get('src'), MAIN_WEBSITE) if preview_image else '',
            }
            if md:
                data['description'] = markdownify(data['description'])
            result.append(data)

    await session.close()
    return result


@news_app.get('/id{news_id:int}')
async def get_all_news(news_id: int, md: bool = False):
    session = ClientSession()
    result = {}

    async with (session.get(MAIN_WEBSITE_ALL_NEWS + f'?nid={news_id}') as resp):
        page_data = BeautifulSoup(await resp.text())

        preview = page_data.find('span', {'class': 'newsinner_cnt'}).find('img')
        result = {
            'id': news_id,
            'date': page_data.find('div', {'class': 'newsinner_date'}).text.strip(),
            'title': page_data.find('strong', {'class': 'newsinner_title'}).text.strip(),
            'content': clean_styles(page_data.find('span', {'class': 'newsinner_cnt'})).encode_contents(),
            'preview': ''
        }
        result['content'] = result['content'].decode('utf-8').replace('src="/', f'src="{MAIN_WEBSITE}/')
        if preview is not None:
            result['preview'] = preview['src']
            if result['preview'].startswith('/'):
                result['preview'] = f"{MAIN_WEBSITE}{result['preview']}".replace(' ', '%20')
        if md:
            result['content'] = markdownify(result['content'])

    await session.close()
    return result
