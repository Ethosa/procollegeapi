from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import TEACHERS_TIMETABLE
from cache import Classrooms


teacher_app = FastAPI()


@teacher_app.get('/{branch_id:int}')
async def get_teachers_by_branch_id(branch_id: int):
    session = ClientSession()
    teachers = []
    async with session.get(TEACHERS_TIMETABLE) as response:
        page_data = BeautifulSoup(await response.text())
        for option in page_data.find('select', id='prep').find_all('option'):
            if option.get('value') == '0':
                continue
            teachers.append({
                'id': int(option.get('value')),
                'title': option.text.strip()
            })
    await session.close()
    return teachers


def query_split(x: str) -> list[str]:
    return x.split('=')


def query_name_in(x: str, right_names: list[str]) -> list[str]:
    return x.split('=')[0] in right_names


@teacher_app.get('/{branch_id:int}/id{teacher_id:int}')
async def get_teacher_week_by_id(
        branch_id: int,
        teacher_id: int,
        day: int | None = None,
        month: int | None = None,
        year: int | None = None
):
    session = ClientSession()
    result = {'days': []}
    if day is None or month is None or year is None:
        query = f'?dep={branch_id}&prep_id={teacher_id}'
    else:
        query = f'?dep={branch_id}&prep_id={teacher_id}&d={day}&m={month}&y={year}'
    async with session.get(TEACHERS_TIMETABLE + query) as response:
        page_data = BeautifulSoup(await response.text())
        table = page_data.find('table', {'class': 'main'})
        main_content = page_data.find('div', {'role': 'main'})
        literals = list('dym')
        previous_queries = list(filter(
            lambda x: query_name_in(x, literals),
            main_content.find_all()[9].get('href').replace('\r\n', '').split('?')[1].split('&'),
        ))
        next_queries = list(filter(
            lambda x: query_name_in(x, literals),
            main_content.find_all()[11].get('href').replace('\r\n', '').split('?')[1].split('&'),
        ))
        result['next'] = {i[0]: i[1] for i in list(map(query_split, next_queries))}
        result['prev'] = {i[0]: i[1] for i in list(map(query_split, previous_queries))}
        for (i, tr) in enumerate(table.find_all('tr')):
            children = tr.find_all('td')
            if i == 0:
                result['teacher'] = children[1].text.strip()
                continue
            elif i == 1:
                continue
            if len(children) == 5:
                result['days'].append({
                    'title': children[0].text.strip(), 'lessons': [{
                        'number': children[1].text.strip(),
                        'classroom': children[2].text.strip(),
                        'group': children[3].text.strip(),
                        'title': children[4].text.strip(),
                        'start': '',
                        'end': '',
                    }]
                })
                if Classrooms.branches:
                    lesson_index = len(result['days'][-1]['lessons'])-1
                    day_index = len(result['days'])-1
                    number = result['days'][-1]['lessons'][-1]['number'].strip()
                    group = result['days'][-1]['lessons'][-1]['group'].strip()
                    classroom = result['days'][-1]['lessons'][-1]['classroom'].strip()
                    for group_id in Classrooms.branches[branch_id].keys():
                        if Classrooms.branches[branch_id][group_id]['name'] != group:
                            continue
                        if len(Classrooms.branches[branch_id][group_id]['week']) <= day_index:
                            continue
                        for lesson in Classrooms.branches[branch_id][group_id]['week'][day_index]['lessons']:
                            if lesson['room'] == classroom and lesson['number'] == number:
                                result['days'][-1]['lessons'][-1]['start'] = lesson['start']
                                result['days'][-1]['lessons'][-1]['end'] = lesson['end']
                                break
            elif len(result['days']) > 0:
                result['days'][-1]['lessons'].append({
                    'number': children[0].text.strip(),
                    'classroom': children[1].text.strip(),
                    'group': children[2].text.strip(),
                    'title': children[3].text.strip(),
                    'start': '',
                    'end': '',
                })
                if Classrooms.branches:
                    lesson_index = len(result['days'][-1]['lessons'])-1
                    day_index = len(result['days'])-1
                    group = result['days'][-1]['lessons'][-1]['group'].strip()
                    classroom = result['days'][-1]['lessons'][-1]['classroom'].strip()
                    number = result['days'][-1]['lessons'][-1]['number'].strip()
                    for group_id in Classrooms.branches[branch_id].keys():
                        if Classrooms.branches[branch_id][group_id]['name'] != group:
                            continue
                        if len(Classrooms.branches[branch_id][group_id]['week']) <= day_index:
                            continue
                        for lesson in Classrooms.branches[branch_id][group_id]['week'][day_index]['lessons']:
                            if lesson['room'] == classroom and lesson['number'] == number:
                                result['days'][-1]['lessons'][-1]['start'] = lesson['start']
                                result['days'][-1]['lessons'][-1]['end'] = lesson['end']
                                break
    await session.close()
    for day in result['days']:
        day['lessons'] = list(filter(lambda x: x['group'], day['lessons']))
    return result
