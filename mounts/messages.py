import asyncio

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from fastapi import FastAPI, WebSocketException, WebSocket
from fastapi.responses import JSONResponse
from time import time

from constants import (
    MY_DESKTOP, CORE_MESSAGE_GET_CONVERSATIONS, SERVICE,
    CORE_MESSAGE_GET_CONVERSATION_MESSAGES,
    CORE_MESSAGE_SEND_MESSAGES_TO_CONVERSATION
)
from models.messages import NewMessage
from utils import check_auth, error

messages_app = FastAPI()


@messages_app.get('/conversations')
async def get_all_conversations(access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    sess_key: str | None = None
    user_id: str | None = None
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    params = {
        'sesskey': sess_key,
        'info': CORE_MESSAGE_GET_CONVERSATIONS
    }
    data = [{
        'methodname': CORE_MESSAGE_GET_CONVERSATIONS,
        'index': 0,
        'args': {
            "userid": user_id,
            "type": 1,
            "limitnum": 51,
            "limitfrom": 0,
            "favourites": False,
            "mergeself": True
        }
    }]
    conversations = []
    async with session.post(SERVICE, params=params, json=data, headers=_headers) as response:
        data = await response.json()
        for i in data[0]['data']['conversations']:
            conversations.append({
                'title': i['members'][0]['fullname'],
                'id': i['members'][0]['id'],
                'chat_id': i['id'],
                'image': i['members'][0]['profileimageurl'],
                'type': 'private',
                'last_message': {
                    'text': BeautifulSoup(i['messages'][-1]['text']).text,
                    'time': i['messages'][-1]['timecreated'],
                    'from': i['messages'][-1]['useridfrom'],
                    'is_you': user_id == str(i['messages'][-1]['useridfrom'])
                },
            })
    await session.close()
    return conversations


@messages_app.get('/history/{chat_id:int}')
async def get_all_conversations(access_token: str, chat_id: int):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    sess_key: str | None = None
    user_id: str | None = None
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    params = {
        'sesskey': sess_key,
        'info': CORE_MESSAGE_GET_CONVERSATION_MESSAGES
    }
    data = [{
        'methodname': CORE_MESSAGE_GET_CONVERSATION_MESSAGES,
        'index': 0,
        'args': {
            "convid": chat_id,
            "currentuserid": user_id,
            "limitnum": 101,
            "limitfrom": 0,
            "newest": True
        }
    }]
    result = {}
    async with session.post(SERVICE, params=params, json=data, headers=_headers) as response:
        result = await response.json()
    await session.close()
    return result


@messages_app.post('/send/{chat_id:int}')
async def get_all_conversations(access_token: str, chat_id: int, msg: NewMessage):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    sess_key: str | None = None
    user_id: str | None = None
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    params = {
        'sesskey': sess_key,
        'info': CORE_MESSAGE_SEND_MESSAGES_TO_CONVERSATION
    }
    data = [{
        'methodname': CORE_MESSAGE_SEND_MESSAGES_TO_CONVERSATION,
        'index': 0,
        'args': {
            "conversationid": chat_id,
            "messages": [{
                'text': msg.text
            }]
        }
    }]
    result = {}
    async with session.post(SERVICE, params=params, json=data, headers=_headers) as response:
        result = await response.json()
    await session.close()
    return result[0]['data'][0]


async def get_user_data(access_token: str) -> dict:
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    sess_key: str | None = None
    user_id: str | None = None
    async with session.get(MY_DESKTOP, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        user_id = page_data.find('div', id='nav-notification-popover-container').get('data-userid')
    await session.close()
    return {
        'sess_key': sess_key,
        'user_id': user_id
    }


@messages_app.websocket('/listen/{chat_id:int}')
async def listen_chat(ws: WebSocket, access_token: str, chat_id: int):
    await ws.accept()
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        await ws.send_bytes(_headers.body)
        await ws.close()
        return
    session = ClientSession()
    user_data = await get_user_data(access_token)
    try:
        while True:
            await ws.receive()
            params = {
                'sesskey': user_data['sess_key'],
                'info': CORE_MESSAGE_GET_CONVERSATION_MESSAGES
            }
            data = [{
                'methodname': CORE_MESSAGE_GET_CONVERSATION_MESSAGES,
                'index': 0,
                'args': {
                    "convid": chat_id,
                    "currentuserid": user_data['user_id'],
                    "limitnum": 101,
                    "limitfrom": 0,
                    'timefrom': round(time()),
                    "newest": True
                }
            }]
            result = {}
            async with session.post(SERVICE, params=params, json=data, headers=_headers) as response:
                result = (await response.json())[0]
            if 'error' in result and result['error']:
                if result['exception'] == 'servicerequireslogin':
                    await ws.send_json({
                        'error': 'require authorization'
                    })
            elif 'data' in result:
                await ws.send_json(result['data'])
                current_time = time()
    except WebSocketException as e:
        pass
    await session.close()
