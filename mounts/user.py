from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from api import (
    LOGIN_URL, USER_AGENT_HEADERS,
    MY_DESKTOP, CORE_MESSAGE_GET_CONVERSATIONS,
    SERVICE, PROFILE_TIMETABLE
)
from models.user import LoginUser, Signed
from utils import error, headers, get_moodle


user_app = FastAPI()


@user_app.post('/login')
async def sign_in(user: LoginUser):
    login_token: str | None = None
    user_id: str | None = None
    session = ClientSession()
    try:
        async with session.get(LOGIN_URL, headers=USER_AGENT_HEADERS) as response:
            page_data = BeautifulSoup(await response.text())
            form_data = page_data.find('form', id='login')
            user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
            login_token = form_data.find('input', {'name': 'logintoken'}).get('value')
    except Exception as e:
        print(e)
    if not login_token:
        await session.close()
        return error('Произошла неизвестная ошибка, попробуйте позже.')
    token: str | None = None
    _headers = headers()
    try:
        async with session.post(LOGIN_URL, headers=USER_AGENT_HEADERS, data={
            'anchor': '',
            'logintoken': login_token,
            'username': user.login,
            'password': user.password
        }) as response:
            cookies = session.cookie_jar.filter_cookies('https://pro.kansk-tc.ru')
            for key, val in cookies.items():
                _headers['Cookie'] = val.value
                token = key.replace('MoodleSession', '') + ':' + val.value
    except Exception as e:
        print(e)
        await session.close()
        return error('Произошла неизвестная ошибка, попробуйте позже.')
    await session.close()
    return {
        'access_token': token,
        'user_id': int(user_id) if user_id else 0
    }


@user_app.get('/info')
async def get_user_info(access_token: str):
    if not access_token:
        return error('Вы не авторизованы')
    session = ClientSession()
    moodle = get_moodle(access_token)
    _headers = headers({
        'Cookie': moodle['cookie']
    })
    main_info = {}
    user_info = {}
    courses = []
    today = {}
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        main_info_div = page_data.find('div', id='d-info')
        for i in main_info_div.find_all('tr'):
            main_info[i.th.text] = i.td.text.strip()
        user_menu = page_data.find('a', id='usermenu')
        if user_menu is not None:
            user_info['name'] = user_menu.span.text.strip()
            user_info['image'] = page_data.find('img', {'class': 'userpicture'}).get('src')
        courses_data = page_data.find('div', id='d-course')
        for course in courses_data.find_all('div', {'class': 'block-years'}):
            data = {
                'title': course.find('div', {'class': 'course-title'}).text.strip(),
                'courses': []
            }
            for c in course.find_all('div', {'class': 'course-container'}):
                # print(c.contents[-1])
                data['courses'].append({
                    'title': c.a.text.strip(),
                    'teacher': c.contents[-1].strip()
                })
            courses.append(data)
        today_data = page_data.find('div', id='d-timetable')
        today = {
            'title': today_data.h3.text.strip(),
            'lessons': [],
            'minutes': 0,
        }
        for lesson in today_data.find_all('div', {'class': 'd-lesson'}):
            lesson_time = lesson.find('div', {'class': 'lesson-time'})
            if lesson_time:
                frm = lesson_time.contents[0].text.split(':')
                to = lesson_time.contents[-1].text.split(':')
                frm_minutes = int(frm[0])*60 + int(frm[1])
                to_minutes = int(to[0])*60 + int(to[1])
                today['minutes'] += to_minutes - frm_minutes
            today['lessons'].append({
                'number': lesson.find('div', {'class': 'lesson-number'}).text.strip(),
                'lesson_time': [lesson_time.contents[0].text.strip(), lesson_time.contents[-1].text.strip()],
                'teacher': lesson.find('div', {'class': 'lesson-group'}).text.strip(),
                'title': lesson.find('div', {'class': 'lesson-course'}).a.text.strip(),
                'classroom': lesson.find('div', {'class': 'lesson-classroom'}).text.strip()
            })
    await session.close()
    return {
        'main_info': main_info,
        'user_info': user_info,
        'today': today,
        'courses': courses
    }


@user_app.get('/day/{day_number:int}')
async def get_timetable_for_day(access_token: str, day_number: int = 0):
    if not access_token:
        return error('Вы не авторизованы')
    session = ClientSession()
    moodle = get_moodle(access_token)
    _headers = headers({
        'Cookie': moodle['cookie']
    })
    user_id: str | None = None
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    today = {}
    params = {
        'user': user_id,
        'day': day_number,
    }
    async with session.get(PROFILE_TIMETABLE, params=params, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        today = {
            'title': page_data.h3.text.strip(),
            'lessons': [],
            'minutes': 0,
        }
        for lesson in page_data.find_all('div', {'class': 'd-lesson'}):
            lesson_time = lesson.find('div', {'class': 'lesson-time'})
            if lesson_time:
                frm = lesson_time.contents[0].text.split(':')
                to = lesson_time.contents[-1].text.split(':')
                frm_minutes = int(frm[0])*60 + int(frm[1])
                to_minutes = int(to[0])*60 + int(to[1])
                today['minutes'] += to_minutes - frm_minutes
            today['lessons'].append({
                'number': lesson.find('div', {'class': 'lesson-number'}).text.strip(),
                'lesson_time': [lesson_time.contents[0].text.strip(), lesson_time.contents[-1].text.strip()],
                'teacher': lesson.find('div', {'class': 'lesson-group'}).text.strip(),
                'title': lesson.find('div', {'class': 'lesson-course'}).a.text.strip(),
                'classroom': lesson.find('div', {'class': 'lesson-classroom'}).text.strip()
            })
    await session.close()
    return today


@user_app.get('/conversations')
async def get_all_conversations(access_token: str):
    if not access_token:
        return error('Вы не авторизованы')
    session = ClientSession()
    moodle = get_moodle(access_token)
    _headers = headers({
        'Cookie': moodle['cookie']
    })
    sess_key: str | None = None
    user_id: str | None = None
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    params = {
        'sesskey': sess_key,
        'info': CORE_MESSAGE_GET_CONVERSATIONS
    }
    data = [{
        'methodname': CORE_MESSAGE_GET_CONVERSATIONS,
        'index': 0,
        'args': {
            "userid": user_id,
            "type": 1,
            "limitnum": 51,
            "limitfrom": 0,
            "favourites": False,
            "mergeself": True
        }
    }]
    conversations = []
    async with session.post(SERVICE, params=params, json=data, headers=_headers) as response:
        data = await response.json()
        for i in data[0]['data']['conversations']:
            conversations.append({
                'title': i['members'][0]['fullname'],
                'id': i['members'][0]['id'],
                'image': i['members'][0]['profileimageurl'],
                'type': 'private',
                'last_message': {
                    'text': BeautifulSoup(i['messages'][-1]['text']).text,
                    'time': i['messages'][-1]['timecreated'],
                    'from': i['messages'][-1]['useridfrom'],
                    'you': user_id == str(i['messages'][-1]['useridfrom'])
                },
            })
    if not access_token:
        return error('Произошла неизвестная ошибка, попробуйте позже')
    await session.close()
    return {
        "conversations": conversations
    }
