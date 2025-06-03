from fastapi import FastAPI
from aiohttp import ClientSession
from markdownify import markdownify
from bs4 import BeautifulSoup

from constants import MAIN_WEBSITE, MAIN_WEBSITE_ALL_NEWS
from utils import beautify_src, clean_styles, proxify
from cache import cache_request, NewsCache

news_app = FastAPI()


@news_app.get('/')
@cache_request()
async def get_last_college_news(md: bool = False):
    result = []
    async with ClientSession() as session:
        async with session.get(MAIN_WEBSITE) as resp:
            page_data = BeautifulSoup(await resp.text(), features='html5lib')
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
                if not data['preview']:
                    if data['id'] in NewsCache.data:
                        full_data = NewsCache.data[data['id']]
                    else:
                        full_data = await get_new_by_id(news_id=data['id'])
                        NewsCache.data[data['id']] = full_data
                    if full_data['preview']:
                        data['preview'] = full_data['preview']
                if data['preview']:
                    data['preview'] = proxify(data['preview'])
                if md:
                    data['description'] = markdownify(data['description'])
                result.append(data)
    return result


@news_app.get('/full')
@cache_request()
async def get_all_news(page: int = 1, md: bool = False):
    result = []

    async with ClientSession() as session:
        async with session.get(MAIN_WEBSITE_ALL_NEWS + f'?p_cur={page-1}') as resp:
            page_data = BeautifulSoup(await resp.text(), features='html5lib')

            ttnav = page_data.find('div', {'class': 'ttnav bottom'})
            last_page = int(ttnav.find_all('a', {'class': 'anav'})[-1].text)
            current_page = int(ttnav.find('strong').text)

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
                if not data['preview']:
                    if data['id'] in NewsCache.data:
                        full_data = NewsCache.data[data['id']]
                    else:
                        full_data = await get_new_by_id(news_id=data['id'])
                        NewsCache.data[data['id']] = full_data
                    if full_data['preview']:
                        data['preview'] = full_data['preview']
                if data['preview']:
                    data['preview'] = proxify(data['preview'])
                if md:
                    data['description'] = markdownify(data['description'])
                result.append(data)

    return {
        'page': page,
        'pages': last_page if last_page > current_page else current_page,
        'news': result
    }


@news_app.get('/id{news_id:int}')
@cache_request()
async def get_new_by_id(news_id: int, md: bool = False):
    result = {}

    if news_id in NewsCache.data:
        return NewsCache.data[news_id]

    async with ClientSession() as session:
        async with session.get(MAIN_WEBSITE_ALL_NEWS + f'?nid={news_id}') as resp:
            page_data = BeautifulSoup(await resp.text(), features='html5lib')

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
                    result['preview'] = f"{MAIN_WEBSITE}{result['preview']}".replace(' ', '%20'),
                result['preview'] = proxify(result['preview'], None)
            if md:
                result['content'] = markdownify(result['content'])

    NewsCache.data[result['id']] = result
    return result
