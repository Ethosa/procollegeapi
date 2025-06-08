from json import dumps
from re import sub
from datetime import datetime, timedelta

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from aiohttp import ClientSession, ClientTimeout
import collections
collections.Callable = collections.abc.Callable
from bs4 import BeautifulSoup

from mounts.user import user_app
from mounts.branches import branches_app
from mounts.teachers import teacher_app
from mounts.blogs import blogs_app
from mounts.timetable import timetable_app
from mounts.media import media_app
from mounts.news import news_app
from mounts.courses import courses_app
from mounts.messages import messages_app
from mounts.notifications import notifications_app
from mounts.photos import photos_app
from mounts.contacts import contacts_app
from mounts.updates import updates_app
from mounts.status import status_app
from middleware.file_size_limit import LimitUploadSize
from middleware.error_handler import catch_exceptions_middleware

from cache import Classrooms, StatusCache
from constants import CACHE_DIR, LOGIN_URL, MAIN_WEBSITE
from utils import lessons_length


sentry_sdk.init(
    dsn="https://65e5fb73a47437246b455eb666b7ab3f@o4509189598609408.ingest.de.sentry.io/4509189608964176",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)


app = FastAPI()
api_app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_headers="*",
    allow_methods="*",
    allow_origins="*",
    allow_credentials=True
)
app.add_middleware(LimitUploadSize, max_upload_size=1024 * 1024 * 3)  # 3 Mb
api_app.middleware('http')(catch_exceptions_middleware)

api_app.mount('/user', user_app)
api_app.mount('/news', news_app)
api_app.mount('/courses', courses_app)
api_app.mount('/branches', branches_app)
api_app.mount('/teachers', teacher_app)
api_app.mount('/blogs', blogs_app)
api_app.mount('/timetable', timetable_app)
api_app.mount('/messages', messages_app)
api_app.mount('/media', media_app)
api_app.mount('/photos', photos_app)
api_app.mount('/contacts', contacts_app)
api_app.mount('/notifications', notifications_app)
api_app.mount('/updates', updates_app)
api_app.mount('/status', status_app)

app.mount('/api', api_app)



@app.on_event('startup')
@repeat_every(seconds=60 * 5)  # every 5 minutes
async def clean_cache():
    now = datetime.utcnow()
    for file in CACHE_DIR.iterdir():
        if file.is_file():
            mtime = datetime.utcfromtimestamp(file.stat().st_mtime)
            if now - mtime > CACHE_LIFETIME:
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Failed to delete {file}: {e}")


@app.on_event('startup')
@repeat_every(seconds=60*60)  # every hour
async def check_site_availability():
    timeout = ClientTimeout(total=5)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.get(LOGIN_URL) as response:
                StatusCache.update_main_website(True)
        except Exception as e:
            StatusCache.update_main_website(False)
        try:
            async with session.get(MAIN_WEBSITE) as response:
                StatusCache.update_pro_college(True)
        except Exception as e:
            StatusCache.update_pro_college(False)


@app.on_event('startup')
@repeat_every(seconds=60*20)  # every 20 minutes
async def check_classrooms_available():
    session = ClientSession()

    branches = {}
    courses = {}

    # get all branches
    async with session.get('https://pro.kansk-tc.ru/blocks/manage_groups/website/view1.php') as resp:
        page_data = BeautifulSoup(await resp.text(), features='html5lib')
        for i in page_data.find_all('span', {'class': 'spec-select-block'}):
            branch_id = int(i['group_id'])
            branches[branch_id] = {}

    # get all groups by branches
    groups = 'https://pro.kansk-tc.ru/blocks/manage_groups/website/list.php'
    for branch_id in branches.keys():
        courses[branch_id] = []
        async with session.get(f'{groups}?id={branch_id}') as resp:
            page_data = BeautifulSoup(await resp.text(), features='html5lib')
            courses_data = list(page_data.find('div', {'class': 'content'}).children)[-2]
            for course in courses_data.find_all('div', {'class': 'spec-year-block'}):
                course_title = course.find('span', {'class': 'spec-year-name'}).text.strip()
                course_data = {
                    'title': course_title,
                    'groups': []
                }
                for group in course.find_all('span', {'class': 'group-block'}):
                    branches[branch_id][int(group['group_id'])] = {
                        'week': [],
                        'name': group.text.strip(),
                        'course': course_title,
                    }
                    course_data['groups'].append({
                        'id': int(group.get('group_id')),
                        'title': group.text.strip()
                    })
                courses[branch_id].append(course_data)

    timetable = 'https://pro.kansk-tc.ru/blocks/manage_groups/website/view.php?dep=1'
    for branch_id in branches.keys():
        for group_id in branches[branch_id].keys():
            async with session.get(f'{timetable}&gr={group_id}') as resp:
                page_data = BeautifulSoup(await resp.text(), features='html5lib')
                info = dict()
                info['header'] = page_data.find('div', {'class': 'header'}).text.strip()
                info['current_week'] = int(sub(
                    r'\D+', '', page_data.find('div', {'class': 'weekHeader'}).span.text.strip()
                ))
                info['next_week'] = info['current_week'] + 1
                info['previous_week'] = max(0, info['current_week'] - 1)
                for day in page_data.find_all('td'):
                    day_data = {
                        'title': day.find('div', {'class': 'dayHeader'}).text.strip(),
                        'lessons': []
                    }
                    for lesson in day.find_all('div', {'class': 'lessonBlock'}):
                        try:
                            _time = lesson.find('div', {'class': 'lessonTimeBlock'}).find_all('div')
                            lesson_data = lesson.find_all('div', {'class': 'discBlock'})[-1]
                            if lesson_data.find('sup', {'class': 'cancel'}):
                                continue
                            classroom = lesson_data.find('div', {'class': 'discSubgroupClassroom'}).text.strip()
                            day_data['lessons'].append({
                                'number': _time[0].text.strip(),
                                'start': _time[1].text.strip(),
                                'end': _time[2].text.strip(),
                                'classroom': classroom,
                                'teacher': lesson_data.find('div', {'class': 'discSubgroupTeacher'}).text.strip(),
                                'title': lesson_data.find('div', {'class': 'discHeader'}).find('span').text.strip(),
                            })
                            if classroom not in Classrooms.classrooms and classroom not in Classrooms.exclude:
                                Classrooms.classrooms.append(classroom)
                        except Exception:
                            pass
                    lessons_length(day_data)
                    if day_data['hours'] > 0:
                        branches[branch_id][group_id]['week'].append(day_data)
                branches[branch_id][group_id]['info'] = info

    Classrooms.branches = branches
    Classrooms.courses = courses

    with open('branches.json', 'w', encoding='utf-8') as f:
        f.write(dumps(branches))
    await session.close()
