from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import COURSES_PAGE
from utils import check_auth


courses_app = FastAPI()


@courses_app.get('/branch-categories')
async def get_branches(access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    result = []
    async with session.get(COURSES_PAGE, headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        for category in page_data.find_all('h3', {'class': 'categoryname'}):
            result.append({
                'id': int(category.find('a').get('href').split('categoryid=')[1]),
                'title': category.text.strip()
            })
    await session.close()
    return result


@courses_app.get('/{category_id:int}/categories')
async def get_branch_categories(category_id: int, access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    result = []
    async with session.get(COURSES_PAGE + f'?categoryid={category_id}&perpage=1000', headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        for category in page_data.find_all('h3', {'class': 'categoryname'}):
            result.append({
                'id': int(category.find('a').get('href').split('categoryid=')[1]),
                'title': category.text.strip(),
                'type': 'subcategory'
            })
        for category in page_data.find_all('div', {'class': 'coursebox'}):
            result.append({
                'id': int(category.find('h3').find('a').get('href').split('id=')[1]),
                'title': category.find('h3').text.strip(),
                'type': 'course'
            })
    await session.close()
    return result
