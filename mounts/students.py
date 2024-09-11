from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup


students_app = FastAPI()


@students_app.get('/{branch_id:int}')
async def get_courses_by_branch_id(branch_id: int):
    pass
