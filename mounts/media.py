from json import loads
from urllib.parse import quote_plus
from secrets import token_hex
from os import remove
from secrets import token_hex
from os.path import splitext, exists
from pathlib import Path
from datetime import datetime, timedelta

from aiohttp import ClientSession, MultipartWriter
import aiofiles
from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import JSONResponse, FileResponse
from starlette.background import BackgroundTask

from constants import (
    UPLOAD_TO_REPOSITORY, PROFILE_PAGE, USER_AGENT_HEADERS,
    CACHE_DIR, CACHE_LIFETIME
)
from utils import check_auth, error, get_cached_filename


media_app = FastAPI()


@media_app.post('/avatar')
async def upload_avatar(access_token: str, file: UploadFile):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    params = []
    file_data = file.file.read()
    async with session.get(PROFILE_PAGE, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text(), features='html5lib')
        sess_key = page_data.find('input', {'name': 'sesskey'}).get('value')
        ctx_id = page_data.find('input', {'name': 'context'}).get('value')
        image_file = page_data.find('input', {'name': 'imagefile'}).get('value')
        author = page_data.find('a', {'id': 'usermenu'}).get('title')
        page_data = page_data.find('div', {'id': 'adaptable-tab-editprofile'})
        for inp in page_data.find_all('input', {'type': 'hidden'}):
            params.append((inp.get('name'), inp.get('value')))
        params.append(('description_editor[text]', page_data.find(
            'textarea', {'name': 'description_editor[text]'}
        ).encode_contents()))
        params.append(('city', page_data.find('input', {'name': 'city'}).get('value')))
        for i in page_data.find('select', {'name': 'interests[]'}).find_all('option'):
            params.append(('interests[]', i.get('value')))
        params.append(('imagealt', page_data.find('input', {'name': 'imagealt'}).get('value')))
        params.append(('submitbutton', 'Обновить профиль'))
    with MultipartWriter() as mp:
        mp.append(file_data, {
            'Content-Disposition': f'form-data; name="repo_upload_file"; filename="{file.filename}"',
            'Content-Type': file.content_type
        })
        mp.append(sess_key, {'Content-Disposition': 'form-data; name="sesskey"'})
        mp.append('4', {'Content-Disposition': 'form-data; name="repo_id"'})
        mp.append(image_file, {'Content-Disposition': 'form-data; name="itemid"'})
        mp.append(author, {'Content-Disposition': 'form-data; name="author"'})
        mp.append('/', {'Content-Disposition': 'form-data; name="savepath"'})
        mp.append(file.filename, {'Content-Disposition': 'form-data; name="title"'})
        mp.append(ctx_id, {'Content-Disposition': 'form-data; name="ctx_id"'})
        for accepted_type in ['.gif', '.jpe', '.jpeg', '.jpg', '.png', '.svg', '.svgz']:
            mp.append(accepted_type, {'Content-Disposition': 'form-data; name="accepted_types[]"'})
        _headers['Priority'] = 'u=1, i'
        _headers['Content-Type'] = 'multipart/form-data; boundary=' + mp.boundary
        async with session.post(UPLOAD_TO_REPOSITORY, data=mp, headers=_headers) as response:
            result = loads((await response.text()).replace('\\', ''))
    if 'error' in result:
        return JSONResponse(result, status_code=400)
    query = []
    for i in params:
        query.append(quote_plus(i[0]) + '=' + quote_plus(i[1]))
    _headers['Content-Type'] = 'application/x-www-form-urlencoded'
    _headers['Upgrade-Insecure-Requests'] = '1'
    await session.post('https://pro.kansk-tc.ru/user/profile.php', headers=_headers, data='&'.join(query))
    await session.close()
    return {'response': 'success'}


@media_app.get('/proxy/file')
async def proxy_file_get(request: Request, link: str, access_token: str = None):
    cached_file = Path(get_cached_filename(link))
    if cached_file.exists():
        if datetime.utcnow() - datetime.utcfromtimestamp(cached_file.stat().st_mtime) < CACHE_LIFETIME:
            return FileResponse(cached_file)

    headers = USER_AGENT_HEADERS
    if access_token:
        auth_result = await check_auth(access_token)
        if isinstance(auth_result, JSONResponse):
            return auth_result
        headers = auth_result
    
    for key in request.query_params._dict.keys():
        if key not in ['access_token', 'link']:
            if '&' in link or '?' in link:
                link += f'&{key}={request.query_params._dict[key]}'
            else:
                link += f'?{key}={request.query_params._dict[key]}'

    async with ClientSession() as session:
        async with session.get(link, headers=headers) as resp:
            if resp.status < 200 or resp.status >= 400:
                return error(f'Failed to fetch file: {link}', resp.status)
            async with aiofiles.open(cached_file, 'wb') as f:
                await f.write(await resp.read())

    return FileResponse(cached_file)
