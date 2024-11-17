from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from aiohttp import ClientSession
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
from middleware.file_size_limit import LimitUploadSize
from middleware.error_handler import catch_exceptions_middleware

from cache import Classrooms


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_headers="*",
    allow_methods="*",
    allow_origins="*",
    allow_credentials=True
)
app.add_middleware(LimitUploadSize, max_upload_size=1024 * 1024 * 3)  # 3 Mb
app.middleware('http')(catch_exceptions_middleware)

app.mount('/user', user_app)
app.mount('/news', news_app)
app.mount('/courses', courses_app)
app.mount('/branches', branches_app)
app.mount('/teachers', teacher_app)
app.mount('/blogs', blogs_app)
app.mount('/timetable', timetable_app)
app.mount('/messages', messages_app)
app.mount('/media', media_app)
app.mount('/photos', photos_app)
app.mount('/contacts', contacts_app)
app.mount('/notifications', notifications_app)
app.mount('/updates', updates_app)


@app.on_event('startup')
@repeat_every(seconds=60*60)
async def check_classrooms_available():
    session = ClientSession()

    branches = {}

    # get all branches
    async with session.get('https://pro.kansk-tc.ru/blocks/manage_groups/website/view1.php') as resp:
        page_data = BeautifulSoup(await resp.text())
        for i in page_data.find_all('span', {'class': 'spec-select-block'}):
            branch_id = int(i['group_id'])
            branches[branch_id] = {}

    # get all groups by branches
    groups = 'https://pro.kansk-tc.ru/blocks/manage_groups/website/list.php'
    for branch_id in branches.keys():
        async with session.get(f'{groups}?id={branch_id}') as resp:
            page_data = BeautifulSoup(await resp.text())
            for i in page_data.find_all('span', {'class': 'group-block'}):
                branches[branch_id][int(i['group_id'])] = []

    timetable = 'https://pro.kansk-tc.ru/blocks/manage_groups/website/view.php?dep=1'
    for branch_id in branches.keys():
        for group_id in branches[branch_id].keys():
            async with session.get(f'{timetable}&gr={group_id}') as resp:
                page_data = BeautifulSoup(await resp.text())
                for day in page_data.find_all('td'):
                    day_data = {
                        'title': day.find('div', {'class': 'dayHeader'}).text.strip(),
                        'lessons': []
                    }
                    for lesson in day.find_all('div', {'class': 'lessonBlock'}):
                        try:
                            _time = lesson.find('div', {'class': 'lessonTimeBlock'}).find_all('div')
                            classroom = lesson.find('div', {'class': 'discSubgroupClassroom'}).text.strip()
                            day_data['lessons'].append({
                                'number': _time[0].text.strip(),
                                'start': _time[1].text.strip(),
                                'end': _time[2].text.strip(),
                                'room': classroom,
                                'teacher': lesson.find('div', {'class': 'discSubgroupTeacher'}).text.strip(),
                                'title': lesson.find('div', {'class': 'discHeader'}).text.strip(),
                            })
                            if classroom not in Classrooms.classrooms and classroom not in Classrooms.invalid:
                                Classrooms.classrooms.append(classroom)
                        except Exception:
                            pass
                    branches[branch_id][group_id].append(day_data)

    Classrooms.branches = branches
    await session.close()
