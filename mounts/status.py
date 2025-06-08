from aiohttp import ClientSession
from fastapi import FastAPI

from cache import StatusCache


status_app = FastAPI()



@status_app.get('/website')
async def is_college_website_working():
    percent = 100.0
    if len(StatusCache.main_website) > 0:
        percent = (
            len(list(filter(lambda x: x, StatusCache.main_website))) /
            len(StatusCache.main_website)
        ) * 100

    return {
        'percent': percent,
        'availability': StatusCache.main_website,
        'now': StatusCache.main_website[-1] if len(StatusCache.main_website) > 0 else True
    }


@status_app.get('/procollege')
async def is_college_website_working():
    percent = 100.0
    if len(StatusCache.pro_college) > 0:
        percent = (
            len(list(filter(lambda x: x, StatusCache.pro_college))) /
            len(StatusCache.pro_college)
        ) * 100

    return {
        'percent': percent,
        'availability': StatusCache.pro_college,
        'now': StatusCache.pro_college[-1] if len(StatusCache.pro_college) > 0 else True
    }
