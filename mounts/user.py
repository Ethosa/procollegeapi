from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from urllib.parse import quote_plus

from constants import (
    LOGIN_URL, USER_AGENT_HEADERS,
    MY_DESKTOP, CORE_MESSAGE_GET_CONVERSATIONS,
    SERVICE, PROFILE_TIMETABLE, PROFILE_PAGE
)
from models.user import LoginUser, EditUser
from utils import error, headers, check_auth


user_app = FastAPI()


@user_app.post('/login')
async def sign_in(user: LoginUser):
    login_token: str | None = None
    user_id: str | None = None
    session = ClientSession()
    already_authed: bool= False
    token: str | None = None
    try:
        async with session.get(LOGIN_URL, headers=USER_AGENT_HEADERS) as response:
            data = await response.text()
            _headers = response.headers
            print(response.headers)
            with open('additional-data.html', 'w', encoding='utf-8') as f:
                f.write(str(USER_AGENT_HEADERS) + '\n\n\n\n\n' + '\n'.join({
                    i[0]: str(i[1])
                    for i in session.headers.items()
                }))
            with open('login_page.html', 'w', encoding='utf-8') as f:
                f.write(data)
            with open('response.html', 'w', encoding='utf-8') as f:
                f.write(str(response.raw_headers))
            if _headers and 'Set-Cookie' in _headers:
                for header in _headers['Set-Cookie'].split(';'):
                    if header.startswith('MoodleSession'):
                        key, value = header.split('=')
                        token = key.replace('MoodleSession', '') + ':' + value
                        break
            page_data = BeautifulSoup(data)
            if token and page_data.find('form', {'action': 'https://pro.kansk-tc.ru/login/logout.php'}):
                already_authed = True
            else:
                form_data = page_data.find('form', id='login')
                login_token = form_data.find('input', {'name': 'logintoken'}).get('value')
    except Exception as e:
        print('after login url', e)
    if already_authed:
        async with session.get(MY_DESKTOP, headers=_headers) as response:
            page_data = BeautifulSoup(await response.text())
            _user_id = page_data.find('div', id='nav-notification-popover-container')
            if _user_id is not None:
                user_id = _user_id.get('data-userid')
            if user_id is None:
                await session.close()
                return error('Произошла неизвестная ошибка, попробуйте позже.')
        await session.close()
        return {
            'access_token': token,
            'user_id': int(user_id) if user_id else 0
        }
    if not login_token:
        await session.close()
        return error('Произошла неизвестная ошибка, попробуйте позже.')
    _headers = headers()
    try:
        err = None
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
            page_data = BeautifulSoup(await response.text())
            if page_data is not None:
                err = page_data.find('a', {'id': 'loginerrormessage'})
        if err is not None:
            await session.close()
            return error(err.text.strip())
    except Exception as e:
        print('after post login url', e)
        await session.close()
        return error('Произошла неизвестная ошибка, попробуйте позже.')
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        _user_id = page_data.find('div', id='nav-notification-popover-container')
        if _user_id is not None:
            user_id = _user_id.get('data-userid')
        if user_id is None:
            await session.close()
            return error('Произошла неизвестная ошибка, попробуйте позже.')
    await session.close()
    return {
        'access_token': token,
        'user_id': int(user_id) if user_id else 0
    }


@user_app.get('/info')
async def get_user_info(access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
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


@user_app.get('/profile')
async def get_user_profile(access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    profile_data = {}
    async with session.get(PROFILE_PAGE, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        user_image = page_data.find('img', {'class': 'userpicture'})
        if user_image is not None and user_image.img is not None:
            profile_data['image'] = user_image.get('src')
        profile_data['full_name'] = page_data.find('li', {'class': 'fullname'}).text.strip()
        email_data = page_data.find('li', {'class': 'email'})
        if email_data is not None:
            profile_data['email'] = email_data.dl.dd.text.strip()
        interests_data = page_data.find('li', {'class': 'interests'})
        if interests_data is not None:
            interests = []
            for li in interests_data.find_all('li'):
                interests.append(li.text.strip())
            profile_data['interests'] = interests
        profile_description_node = page_data.find('li', {'class': 'description'})
        if profile_description_node is not None:
            profile_data['description'] = profile_description_node.dl.dd.encode_contents()
        first_access_request = page_data.find('li', {'class': 'firstaccess'})
        if first_access_request is not None:
            profile_data['first_access_request'] = first_access_request.dl.dd.text.strip()
        last_access_request = page_data.find('li', {'class': 'lastaccess'})
        if last_access_request is not None:
            profile_data['first_access_request'] = last_access_request.dl.dd.text.strip()
    await session.close()
    return profile_data


@user_app.patch('/profile')
async def edit_user_profile(access_token: str, user_data: EditUser):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    params = []
    async with session.get(PROFILE_PAGE, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text()).find('div', {'id': 'adaptable-tab-editprofile'})
        for inp in page_data.find_all('input', {'type': 'hidden'}):
            params.append((inp.get('name'), inp.get('value')))
        if user_data.description is None:
            params.append(('description_editor[text]', page_data.find(
                'textarea', {'name': 'description_editor[text]'}
            ).encode_contents()))
        else:
            params.append(('description_editor[text]', user_data.description))
        if user_data.city is None:
            params.append(('city', page_data.find('input', {'name': 'city'}).get('value')))
        else:
            params.append(('city', user_data.city))
        if user_data.interests is None:
            for i in page_data.find('select', {'name': 'interests[]'}).find_all('option'):
                params.append(('interests[]', i.get('value')))
        else:
            for interest in user_data.interests:
                params.append(('interests[]', interest))
        params.append(('imagealt', page_data.find('input', {'name': 'imagealt'}).get('value')))
        params.append(('submitbutton', 'Обновить профиль'))
    query = []
    for i in params:
        query.append(quote_plus(i[0]) + '=' + quote_plus(i[1]))
    _headers['Content-Type'] = 'application/x-www-form-urlencoded'
    _headers['Upgrade-Insecure-Requests'] = '1'
    await session.post('https://pro.kansk-tc.ru/user/profile.php', headers=_headers, data='&'.join(query))
    await session.close()
    return {'response': 'success'}


@user_app.get('/day/{day_number:int}')
async def get_timetable_for_day(access_token: str, day_number: int = 0):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
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
