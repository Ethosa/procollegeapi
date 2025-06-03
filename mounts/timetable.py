from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from re import match, sub
from datetime import datetime

from constants import STUDENTS_TIMETABLE_GROUPS, STUDENTS_TIMETABLE_GROUP
from cache import Classrooms, cache_request
from utils import error, lessons_length


timetable_app = FastAPI()


@timetable_app.get('/students/courses/{branch_id:int}')
@cache_request()
async def get_courses_by_branch_id(branch_id: int):
    if Classrooms.courses:
        return Classrooms.courses[branch_id]

    session = ClientSession()
    courses = []
    params = {
        'id': branch_id
    }
    async with session.get(STUDENTS_TIMETABLE_GROUPS, params=params) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
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
@cache_request()
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
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        result['header'] = page_data.find('div', {'class': 'header'}).text.strip()
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
                if disc.find('sup', {'class': 'cancel'}):
                    continue
                if len(list(disc.children)) == 0:
                    continue
                time_data = list(lesson.find('div', {'class': 'lessonTimeBlock'}).children)
                lesson_data = {
                    'number': time_data[1].text.strip(),
                    'start': time_data[3].text.strip(),
                    'end': time_data[5].text.strip(),
                    'title': disc.find('div', {'class': 'discHeader'}).find('span').text.strip(),
                    'teacher': disc.find('div', {'class': 'discSubgroupTeacher'}).text.strip(),
                    'classroom': disc.find('div', {'class': 'discSubgroupClassroom'}).text.strip(),
                }
                day_data['lessons'].append(lesson_data)
            lessons_length(day_data)
            if day_data['hours'] > 0:
                result['days'].append(day_data)
    await session.close()
    return result


@timetable_app.get('/students/courses/{branch_id:int}/group/{group_id:int}')
@cache_request()
async def get_timetable_by_group_id(branch_id: int, group_id: int):
    if Classrooms.branches and branch_id in Classrooms.branches and group_id in Classrooms.branches[branch_id]:
        return {
            'header': Classrooms.branches[branch_id][group_id]['info']['header'],
            'current_week': Classrooms.branches[branch_id][group_id]['info']['current_week'],
            'next_week': Classrooms.branches[branch_id][group_id]['info']['next_week'],
            'previous_week': Classrooms.branches[branch_id][group_id]['info']['previous_week'],
            'days': Classrooms.branches[branch_id][group_id]['week']
        }
    return await get_timetable_by_group_id_week(branch_id, group_id, 0)


@timetable_app.get('/classrooms')
@cache_request()
async def get_classrooms_list():
    return Classrooms.classrooms


@timetable_app.get('/classrooms/free')
@cache_request()
async def get_free_classrooms(day: int = -1, time: str | None = None, number: int = -1):
    if day == -1:
        day = datetime.today().weekday()
        if day == 6:
            day = 0
    if day < 0 or day > 5:
        return error('День недели указан неверно. Он должен быть от 0 до 5 (Пн-Сб).')
    free_classrooms = Classrooms.classrooms[::]
    _time = 0
    if time is not None:
        time_h, time_m = time.split(':', 1)
        _time = int(time_h) * 60 * 60 + int(time_m) * 60
    for branch_id in Classrooms.branches.keys():
        for group_id in Classrooms.branches[branch_id].keys():
            if len(Classrooms.branches[branch_id][group_id]['week']) > day:
                _day = Classrooms.branches[branch_id][group_id]['week'][day]['lessons']
                if number == -1 and time is None:
                    for lesson in _day:
                        if lesson['classroom'] in free_classrooms:
                            free_classrooms.remove(lesson['classroom'])
                elif number >= 0 and time is None:
                    for lesson in _day:
                        if lesson['number'] == str(number) and lesson['classroom'] in free_classrooms:
                            free_classrooms.remove(lesson['classroom'])
                elif number == -1 and time is not None:
                    for lesson in _day:
                        start_h, start_m = lesson['start'].split(':')
                        end_h, end_m = lesson['end'].split(':')
                        start_seconds = int(start_h) * 60 * 60 + int(start_m) * 60
                        end_seconds = int(end_h) * 60 * 60 + int(end_m) * 60
                        if start_seconds <= _time <= end_seconds:
                            if lesson['classroom'] in free_classrooms:
                                free_classrooms.remove(lesson['classroom'])
    return free_classrooms


@timetable_app.get('/classrooms/room/{room:str}')
@cache_request()
async def get_classroom_free_for_week(room: str):
    days = []

    for branch_id in Classrooms.branches.keys():
        for group_id in Classrooms.branches[branch_id].keys():
            for day_index, day in enumerate(Classrooms.branches[branch_id][group_id]['week']):
                if len(days) < 6:
                    days.append({'title': day['title'], 'lessons': [
                        {
                            'number': str(i+1),
                            'available': True,
                        }
                        for i in range(7)
                    ]})
                for lesson_index, lesson in enumerate(day['lessons']):
                    if lesson['number'] == days[day_index]['lessons'][lesson_index]['number']:
                        days[day_index]['lessons'][lesson_index]['start'] = lesson['start']
                        days[day_index]['lessons'][lesson_index]['end'] = lesson['end']
                    if lesson['classroom'] == room:
                        for i in days[day_index]['lessons']:
                            if i['number'] == lesson['number']:
                                i['title'] = lesson['title']
                                i['teacher'] = lesson['teacher']
                                i['group'] = (
                                    Classrooms.branches[branch_id][group_id]['name']
                                )
                                i['available'] = False
        for day_index, day in enumerate(days):
            days[day_index]['lessons'] = list(filter(lambda x: 'start' in x, days[day_index]['lessons']))
    return days
