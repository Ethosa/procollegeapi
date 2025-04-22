from fastapi import FastAPI
from aiohttp import ClientSession

updates_app = FastAPI()


@updates_app.get('/check')
async def check_for_updates(prerelease: bool = False):
    release = {}

    async with ClientSession() as session:
        async with session.get('https://api.github.com/repos/horanchikk/ktc-reborn/releases') as resp:
            data = await resp.json()

            for item in data:
                print(item)
                print(item['prerelease'], prerelease)
                if prerelease and item['prerelease']:
                    release = item
                    break
                elif not prerelease:
                    release = item
                    break
    
    release_data = {
        'version': release['name'],
        'description': release['body'],
        'tag_info': 'last release' if not release['prerelease'] else 'pre release'
    }
    if release['assets'] and release['assets'][0]['name'].endswith('.apk'):
        release_data['size'] = release['assets'][0]['size']
        release_data['apkfile'] = release['assets'][0]['browser_download_url']

    return release_data
