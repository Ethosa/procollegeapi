from fastapi import FastAPI
from aiohttp import ClientSession

updates_app = FastAPI()


@updates_app.get('/check')
async def check_for_updates():
    session = ClientSession()

    async with session.get('https://api.github.com/repos/horanchikk/ktc-reborn/releases') as resp:
        data = (await resp.json())[0]
        print(data)

    await session.close()

    return {
        'version': data['name'],
        'description': data['body'],
        'tag_info': 'last release' if not data['prerelease'] else 'pre release',
        'apkfile': (
            data['assets'][0]['browser_download_url']
            if data['assets'] and data['assets'][0]['name'].endswith('.apk')
            else ''
        )
    }
