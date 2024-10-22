from time import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from cache import PhotoCache
from constants import GALLERY_PAGE, USER_AGENT_HEADERS


photos_app = FastAPI()


@photos_app.get('/albums')
async def get_all_albums():
    client = ClientSession()

    if time() - PhotoCache.albums_last_update > PhotoCache.cache_time_secs:
        PhotoCache.albums_last_update = time()
        PhotoCache.albums = []
        async with client.get(GALLERY_PAGE, headers=USER_AGENT_HEADERS) as resp:
            page_data = BeautifulSoup(await resp.text())
            for album in page_data.find_all('a', {'class': 'gallery_cat'}):
                PhotoCache.albums.append({
                    'id': int(album.get('href').split('=')[1]),
                    'title': album.find('div', {'class': 'title'}).text.strip(),
                    'date': album.find('div', {'class': 'date'}).text.strip(),
                    'preview': album.find('img').get('src'),
                })
    await client.close()
    return PhotoCache.albums


@photos_app.get('/{album_id:int}')
async def get_all_albums(album_id: int):
    client = ClientSession()

    if (
        album_id not in PhotoCache.albums_full or
        time() - PhotoCache.albums_full[album_id]['last_update_time'] > PhotoCache.cache_time_secs
    ):
        PhotoCache.albums_full[album_id] = {
            'data': {'title': '', 'photos': []},
            'last_update_time': time()
        }
        async with client.get(GALLERY_PAGE + f'?cid={album_id}', headers=USER_AGENT_HEADERS) as resp:
            page_data = BeautifulSoup(await resp.text())
            PhotoCache.albums_full[album_id]['data']['title'] = page_data.find('h2').text.strip()
            for photo in page_data.find_all('a', {'class': 'gallery_prev'}):
                PhotoCache.albums_full[album_id]['data']['photos'].append(
                    photo.get('href')
                )
    await client.close()
    return PhotoCache.albums_full[album_id]['data']

