from bs4 import BeautifulSoup
from fastapi import FastAPI
from aiohttp import ClientSession
from starlette.responses import JSONResponse

from constants import MY_DESKTOP, GET_NOTIFICATIONS_PAGE, MESSAGE_POPUP_GET_POPUP_NOTIFICATIONS
from utils import check_auth


notifications_app = FastAPI()


@notifications_app.get('/count')
async def get_unread_notifications_count(access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    count = 0
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        count_holder = page_data.find('div', {'id': 'nav-notification-popover-container'})
        if count_holder:
            count_holder = count_holder.find('div', {'class': 'count-container'})
            if count_holder:
                count = int(count_holder.text)
    await session.close()
    return count


@notifications_app.get('/')
async def get_unread_notifications_count(access_token: str, offset: int = 0, limit: int = 50):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    params = {
        'sesskey': sess_key,
        'info': MESSAGE_POPUP_GET_POPUP_NOTIFICATIONS
    }
    json_data = [{
        "index": 0,
        "methodname": "message_popup_get_popup_notifications",
        "args": {
            "limit": limit,
            "offset": offset,
            "useridto": user_id
        }
    }]
    async with session.post(GET_NOTIFICATIONS_PAGE, params=params, headers=_headers, json=json_data) as response:
        data = (await response.json())[0]['data']
    free_keys = [
        'component', 'smallmessage',
        'fullmessagehtml', 'text',
        'eventtype', 'customdata',
        'contexturlname', 'contexturl'
    ]
    for i in range(len(data['notifications'])):
        for key in free_keys:
            if key in data['notifications'][i]:
                del data['notifications'][i][key]
    await session.close()
    return data
