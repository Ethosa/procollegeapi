from json import loads

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from aiohttp import ClientSession, MultipartWriter
from bs4 import BeautifulSoup

from constants import (
    BLOG_PAGE, PUBLISH_BLOG_POST, UPLOAD_TO_REPOSITORY,
    BLOG_POST_EDIT, DELETE_BLOG_POST
)
from utils import check_auth, x_form_urlencoded, clean_styles, match_bad_words, error
from models.blog import NewBlogPost


blogs_app = FastAPI()


@blogs_app.get('/')
async def get_all_blogs(access_token: str, page: int = 1, user_id: int | None = None):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    posts = []
    params = {
        'blogpage': page-1 if page >= 1 else 1
    }
    if user_id is not None:
        params['userid'] = user_id
    pages = 1
    async with session.get(BLOG_PAGE, params=params, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        max_page, min_page = 0, 100_000_00
        for page_item in page_data.find_all('li', {'class': 'page-item'}):
            if page_item.get('data-page-number'):
                num = int(page_item['data-page-number'])
                if num > max_page:
                    max_page = num
                elif num < min_page:
                    min_page = num
        pages = max_page
        for post in page_data.find_all('div', {'class': 'forumpost'}):
            commands = []
            for command in post.find('div', {'class': 'commands'}).find_all('a'):
                if command.text.strip().lower() == 'удалить':
                    commands.append({
                        'id': 'delete',
                        'text': 'Удалить',
                        'entry_id': int(command['href'].split('entryid=')[1])
                    })
            data = {
                'title': post.find('div', {'class': 'topic'}).div.a.text.strip(),
                'avatar': post.find('div', {'class': 'picture'}).a.img.get('src'),
                'author': post.find('div', {'class': 'author'}).a.text.strip(),
                'date': post.find('div', {'class': 'author'}).contents[-1][2:].strip(),
                'commands': commands,
                'raw_content': str(
                    clean_styles(
                        post.find('div', {'class': 'maincontent'}).div.find('div', {'class': 'no-overflow'}),
                        access_token
                    ).encode_contents().decode('utf-8')
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
    return {
        'items': posts,
        'pages': pages
    }


@blogs_app.post('/')
async def publish_new_blog_post(access_token: str, data: str = Form(...), file: list[UploadFile] = None):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    post = NewBlogPost.parse_raw(data)
    if match_bad_words(post.text) or match_bad_words(post.title):
        return error('К сожалению ваш пост содержит нецензурную речь.', 403)
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

    if file:
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


@blogs_app.delete('/{post_id:int}')
async def delete_blog_post_by_id(access_token: str, post_id: int):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    session = ClientSession()
    params = {}
    async with session.get(DELETE_BLOG_POST + str(post_id), headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        form = page_data.find('form', {'action': 'edit.php'})
        if form is None:
            await session.close()
            return error('Похоже у вас нет доступа к этому посту', 403)
        for i in form.find_all('input', {'type': 'hidden'}):
            params[i.get('name')] = i.get('value')
    _headers['Content-Type'] = 'application/x-www-form-urlencoded'
    async with session.post(BLOG_POST_EDIT, headers=_headers, data=x_form_urlencoded(params)) as resp:
        pass
    await session.close()
    return {'response': 'success'}
