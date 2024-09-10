from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from api import BLOG_PAGE
from utils import error, headers, get_moodle


blogs_app = FastAPI()


@blogs_app.get('/{user_id:int}')
async def get_blogs_by_user_id(user_id: int, access_token):
    if not access_token:
        return error('Вы не авторизованы')
    session = ClientSession()
    moodle = get_moodle(access_token)
    _headers = headers({
        'Cookie': moodle['cookie']
    })
    posts = []
    async with session.get(BLOG_PAGE, params={'userid': user_id}, headers=_headers) as response:
        page_data = BeautifulSoup(await response.text())
        for post in page_data.find_all('div', {'class': 'forumpost'}):
            data = {
                'title': post.find('div', {'class': 'topic'}).div.a.text.strip(),
                'avatar': post.find('div', {'class': 'picture'}).a.img.get('src'),
                'author': post.find('div', {'class': 'author'}).a.text.strip(),
                'date': post.find('div', {'class': 'author'}).contents[-1][2:].strip(),
                'raw_content': str(post.find('div', {'class': 'maincontent'}).div.find('div', {'class': 'no-overflow'})),
                'attachments': []
            }
            if post.find('div', {'class': 'attachedimages'}):
                for i in post.find('div', {'class': 'attachedimages'}).children:
                    if i.name == 'img':
                        data['attachments'].append({
                            'type': 'image',
                            'src': i.get('src')
                        })
            print(data)
            posts.append(data)
    await session.close()
    return posts
