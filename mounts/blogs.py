from json import loads

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from aiohttp import ClientSession, MultipartWriter
from bs4 import BeautifulSoup

from constants import BLOG_PAGE, PUBLISH_BLOG_POST, UPLOAD_TO_REPOSITORY
from utils import check_auth, x_form_urlencoded
from models.blog import NewBlogPost


blogs_app = FastAPI()


@blogs_app.get('/')
async def get_all_blogs(access_token):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    posts = []
    async with session.get(BLOG_PAGE, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        for post in page_data.find_all('div', {'class': 'forumpost'}):
            data = {
                'title': post.find('div', {'class': 'topic'}).div.a.text.strip(),
                'avatar': post.find('div', {'class': 'picture'}).a.img.get('src'),
                'author': post.find('div', {'class': 'author'}).a.text.strip(),
                'date': post.find('div', {'class': 'author'}).contents[-1][2:].strip(),
                'raw_content': str(
                    post.find('div', {'class': 'maincontent'}).div.find('div', {'class': 'no-overflow'})
                ),
                'attachments': []
            }
            if (attachments := post.find('div', {'class': 'attachedimages'})) is not None:
                for i in attachments.children:
                    if i.name == 'img':
                        data['attachments'].append({
                            'type': 'image',
                            'src': i.get('src')
                        })
            posts.append(data)
    await session.close()
    return posts


@blogs_app.get('/{user_id:int}')
async def get_blogs_by_user_id(user_id: int, access_token):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    posts = []
    async with session.get(BLOG_PAGE, params={'userid': user_id}, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        for post in page_data.find_all('div', {'class': 'forumpost'}):
            data = {
                'title': post.find('div', {'class': 'topic'}).div.a.text.strip(),
                'avatar': post.find('div', {'class': 'picture'}).a.img.get('src'),
                'author': post.find('div', {'class': 'author'}).a.text.strip(),
                'date': post.find('div', {'class': 'author'}).contents[-1][2:].strip(),
                'raw_content': str(
                    post.find('div', {'class': 'maincontent'}).div.find('div', {'class': 'no-overflow'})
                ),
                'attachments': []
            }
            if (attachments := post.find('div', {'class': 'attachedimages'})) is not None:
                for i in attachments.children:
                    if i.name == 'img':
                        data['attachments'].append({
                            'type': 'image',
                            'src': i.get('src')
                        })
            posts.append(data)
    await session.close()
    return posts


@blogs_app.post('/')
async def publish_new_blog_post(access_token: str, data: str = Form(...), file: list[UploadFile] = File(...)):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    post = NewBlogPost.parse_raw(data)
    data = {
        'action': 'add',
        'submitbutton': 'Сохранить',
        'subject': post.title,
        'summary_editor[text]': post.text,
    }
    session = ClientSession()
    uploaded_files = []
    repository_data = {}

    async with session.get("https://pro.kansk-tc.ru/blog/edit.php?action=add", headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        for i in page_data.find(
                'form', {'action': 'https://pro.kansk-tc.ru/blog/edit.php'}
        ).find_all('input', {'type': 'hidden'}):
            data[i.get('name')] = i.get('value')
        repository_data = {
            'author': page_data.find('a', {'id': 'usermenu'}).get('title').strip(),
            'itemid': page_data.find('input', {'name': 'attachment_filemanager'}).get('value'),
            'sesskey': data['sesskey'],
            'ctx_id': page_data.find('input', {'name': 'context'}).get('value'),
            'client_id': page_data.find('div', {'class': 'filemanager'}).get('id').split('-')[1],
        }

    for f in file:
        file_data = f.file.read()
        with MultipartWriter() as mp:
            mp.append(file_data, {
                'Content-Disposition': f'form-data; name="repo_upload_file"; filename="{f.filename}"',
                'Content-Type': f.content_type
            })
            mp.append(repository_data['sesskey'], {'Content-Disposition': 'form-data; name="sesskey"'})
            mp.append('4', {'Content-Disposition': 'form-data; name="repo_id"'})
            mp.append('', {'Content-Disposition': 'form-data; name="p"'})
            mp.append('', {'Content-Disposition': 'form-data; name="page"'})
            mp.append('public', {'Content-Disposition': 'form-data; name="license"'})
            mp.append('filemanager', {'Content-Disposition': 'form-data; name="env"'})
            mp.append(repository_data['itemid'], {'Content-Disposition': 'form-data; name="itemid"'})
            mp.append(repository_data['author'], {'Content-Disposition': 'form-data; name="author"'})
            mp.append('/', {'Content-Disposition': 'form-data; name="savepath"'})
            mp.append(f.filename, {'Content-Disposition': 'form-data; name="title"'})
            mp.append(repository_data['ctx_id'], {'Content-Disposition': 'form-data; name="ctx_id"'})
            mp.append(repository_data['client_id'], {'Content-Disposition': 'form-data; name="client_id"'})
            mp.append(str(f.size), {'Content-Disposition': 'form-data; name="maxbytes"'})
            mp.append('-1', {'Content-Disposition': 'form-data; name="areamaxbytes"'})
            _headers['Content-Type'] = 'multipart/form-data; boundary=' + mp.boundary
            async with session.post(UPLOAD_TO_REPOSITORY, data=mp, headers=_headers) as response:
                uploaded_files.append(
                    loads((await response.text()).replace('\\', ''))
                )

    data['tags'] = post.tags
    data['publishstate'] = 'draft' if post.is_draft else 'site'

    _headers['Content-Type'] = 'application/x-www-form-urlencoded'
    query = x_form_urlencoded(data)

    await session.post(PUBLISH_BLOG_POST, headers=_headers, data=query)
    await session.close()
    return {'response': 'success', 'uploaded_files': uploaded_files}
