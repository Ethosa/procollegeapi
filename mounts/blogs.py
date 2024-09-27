from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import BLOG_PAGE, PUBLISH_BLOG_POST
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
async def publish_new_blog_post(post: NewBlogPost, access_token: str):
    if isinstance(_headers := await check_auth(access_token), JSONResponse):
        return _headers
    data = {
        'action': 'add',
        'submitbutton': 'Сохранить',
        'subject': post.title,
        'summary_editor[text]': post.text,
    }
    session = ClientSession()

    async with session.get("https://pro.kansk-tc.ru/blog/edit.php?action=add", headers=_headers) as resp:
        page_data = BeautifulSoup(await resp.text())
        for i in page_data.find(
                'form', {'action': 'https://pro.kansk-tc.ru/blog/edit.php'}
        ).find_all('input', {'type': 'hidden'}):
            data[i.get('name')] = i.get('value')

    data['tags'] = post.tags
    data['publishstate'] = 'draft' if post.is_draft else 'site'

    _headers['Content-Type'] = 'application/x-www-form-urlencoded'
    query = x_form_urlencoded(data)

    print(query)

    await session.post(PUBLISH_BLOG_POST, headers=_headers, data=query)
    await session.close()
    return {'response': 'success'}
