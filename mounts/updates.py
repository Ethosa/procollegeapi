from bs4 import BeautifulSoup
from fastapi import FastAPI
from aiohttp import ClientSession
from markdownify import markdownify

from utils import clean_styles

updates_app = FastAPI()


@updates_app.get('/check')
async def check_for_updates(md: bool = False):
    session = ClientSession()

    async with session.get('https://github.com/horanchikk/ktc-reborn/releases') as resp:
        page_data = BeautifulSoup(await resp.text())
        last_version = page_data.find('section').find('h2').text.strip()
        description = clean_styles(page_data.find('section').find(
            'div', {'class': 'markdown-body'}
        )).encode_contents().decode('utf-8')
        tag_info = page_data.select('section>div>:last-child>div>div>div>div>div>:last-child')

    await session.close()

    return {
        'version': last_version,
        'description': markdownify(description) if md else description,
        'tag_info': tag_info[0].text.strip().lower() if tag_info else 'last release'
    }
