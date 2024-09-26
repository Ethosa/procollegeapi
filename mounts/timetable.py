from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from re import match, sub

from constants import STUDENTS_TIMETABLE_GROUPS, STUDENTS_TIMETABLE_GROUP


timetable_app = FastAPI()


@timetable_app.get('/students/courses/{branch_id:int}')
async def get_courses_by_branch_id(branch_id: int):
    session = ClientSession()
    courses = []
    params = {
        'id': branch_id
    }
    async with session.get(STUDENTS_TIMETABLE_GROUPS, params=params) as response:
        page_data = BeautifulSoup(await response.text())
        courses_data = list(page_data.find('div', {'class': 'content'}).children)[-2]
        for course in courses_data.find_all('div', {'class': 'spec-year-block'}):
            data = {
                'title': course.find('span', {'class': 'spec-year-name'}).text.strip(),
                'groups': []
            }
            for group in course.find_all('span', {'class': 'group-block'}):
                data['groups'].append({
                    'id': int(group.get('group_id')),
                    'title': group.text.strip()
                })
            courses.append(data)
    await session.close()
    return courses


@timetable_app.get('/students/courses/{branch_id:int}/group/{group_id:int}/week/{week:int}')
async def get_timetable_by_group_id_week(branch_id: int, group_id: int, week: int = -1):
    session = ClientSession()
    result = {
        'days': []
    }
    params = {
        'dep': branch_id,
        'gr': group_id
    }
    if week > 0:
        params['week'] = week
    async with session.get(STUDENTS_TIMETABLE_GROUP, params=params) as response:
        page_data = BeautifulSoup(await response.text())
        result['header'] = page_data.find('div', {'class': 'header'}).text.strip()
        print(page_data.find('div', {'class': 'weekHeader'}).span.text.strip())
        result['current_week'] = int(sub(
            r'\D+', '', page_data.find('div', {'class': 'weekHeader'}).span.text.strip()
        ))
        result['next_week'] = result['current_week']+1
        result['previous_week'] = max(0, result['current_week']-1)
        for day in page_data.find('div', {'class': 'timetableContainer'}).find_all('td'):
            day_data = {
                'title': day.find('div', {'class': 'dayHeader'}).text.strip(),
                'lessons': []
            }
            for lesson in day.find_all('div', {'class': 'lessonBlock'}):
                disc = list(lesson.find_all('div', {'class': 'discBlock'}))[-1]
                if len(list(disc.children)) == 0:
                    continue
                time_data = list(lesson.find('div', {'class': 'lessonTimeBlock'}).children)
                lesson_data = {
                    'number': int(time_data[1].text.strip()),
                    'start': time_data[3].text.strip(),
                    'end': time_data[5].text.strip(),
                    'title': disc.find('div', {'class': 'discHeader'}).text.strip(),
                    'teacher': disc.find('div', {'class': 'discSubgroupTeacher'}).text.strip(),
                    'classroom': disc.find('div', {'class': 'discSubgroupClassroom'}).text.strip(),
                }
                day_data['lessons'].append(lesson_data)
            result['days'].append(day_data)
    await session.close()
    return result


@timetable_app.get('/students/courses/{branch_id:int}/group/{group_id:int}')
async def get_timetable_by_group_id(branch_id: int, group_id: int):
    return await get_timetable_by_group_id_week(branch_id, group_id, 0)
