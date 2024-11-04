from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import COURSES_PAGE, MY_DESKTOP, VIEW_PAGE
from utils import check_auth, error, clean_styles


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


@courses_app.get('/{course_id:int}')
async def get_course_by_id(course_id: int, access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    result = {
        'title': '',
        'topics': []
    }
    async with session.get(VIEW_PAGE + f'?id={course_id}', headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        notice = page_data.find('div', {'id': 'notice'})
        error_message = page_data.find('p', {'class': 'errormessage'})
        if notice is not None and notice.text.strip().lower() == 'вы не можете записаться на этот курс':
            await session.close()
            return error(notice.text.strip(), 403)
        if error_message is not None:
            await session.close()
            return error(error_message.text.strip(), 400)
        result['title'] = page_data.find('title').text.strip()
        topics = page_data.find('ul', {'class': 'topics'}).find_all('li', {'class': 'section'})
        if topics is None:
            await session.close()
            return error('Курс указан неправильно', 400)
        for topic in topics:
            title = topic.find('h3', {'class': 'sectionname'})
            summary = topic.find('div', {'class': 'summary'})
            topic_data = {
                'title': title.text.strip(),
                'url': title.span.a['href'],
                'summary': clean_styles(summary).encode_contents().decode('utf-8') if summary else '',
                'items': []
            }
            for li in topic.find_all('li', {'class': 'activity'}):
                name = li.find('span', {'class': 'instancename'})
                icon = li.find('img')
                content_after = li.find('div', {'class': 'contentafterlink'})
                content_without_link = li.find('div', {'class': 'contentwithoutlink'})
                link = li.find('a')
                topic_data['items'].append({
                    'name': name.find(text=True, recursive=False).strip() if name else '',
                    'icon': icon['src'] if icon else '',
                    'view_id': int(link['href'].split('?id=')[1]) if link else -1,
                    'content_after': (
                        clean_styles(content_after).encode_contents().decode('utf-8') if content_after else ''
                    ),
                    'content_without_link': (
                        clean_styles(content_without_link).encode_contents().decode('utf-8')
                        if content_without_link else ''
                    ),
                })
            result['topics'].append(topic_data)
    await session.close()
    return result
