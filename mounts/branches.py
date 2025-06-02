from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import TEACHERS_TIMETABLE
from cache import cache_request


branches_app = FastAPI()


def squeeze_title(title: str) -> str:
    return title.replace(
        'Краевое государственное бюджетное профессиональное образовательное учреждение', 'КГБПОУ'
    ).replace(
        'краевого государственного бюджетного профессионального образовательного учреждения', 'КГБПОУ'
    )


@branches_app.get('/')
@cache_request()
async def get_all_branches(squeeze: bool = False):
    session = ClientSession()
    branches = []
    async with session.get(TEACHERS_TIMETABLE) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        for option in page_data.find('select', id='dep').find_all('option'):
            if option.get('value') == '0':
                continue
            branches.append({
                'id': int(option.get('value')),
                'title': squeeze_title(option.text.strip()) if squeeze else option.text.strip()
            })
    await session.close()
    return branches
