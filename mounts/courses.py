from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import COURSES_PAGE, MY_DESKTOP
from utils import check_auth


courses_app = FastAPI()


@courses_app.get('/')
async def get_branch_categories(access_token: str, category_id: int | None = None):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    result = []
    query = f'?categoryid={category_id}&perpage=1000' if category_id else f'?perpage=1000'
    async with session.get(COURSES_PAGE + query, headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        for category in page_data.find_all('h3', {'class': 'categoryname'}):
            result.append({
                'id': int(category.find('a').get('href').split('categoryid=')[1]),
                'title': category.text.strip(),
                'type': 'subcategory'
            })
        for category in page_data.find_all('div', {'class': 'coursebox'}):
            result.append({
                'id': int(category.get('data-courseid')),
                'title': (
                    category.find('h3').text.strip()
                    if category.find('h3') else
                    category.find('div', {'class': 'coursename'}).text.strip()
                ),
                'type': 'course',
                'teachers': [{
                    'name': i.text.strip(),
                    'id': int(i.get('href').split('id=')[1].split('&')[0])
                } for i in category.find('ul').find_all('a')] if category.find('ul') else []
            })
    await session.close()
    return result


@courses_app.get('/my')
async def get_my_courses(access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    result = []
    async with session.get(MY_DESKTOP, headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        for course in page_data.find('ul', {'id': 'dropdownmain-navigation0'}).find_all('li'):
            result.append({
                'id': int(course.find('a').get('href').split('id=')[1].strip()),
                'title': course.find('a').text.strip(),
            })
    await session.close()
    return result
