from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from api import TEACHERS_TIMETABLE


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

