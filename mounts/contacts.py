from re import findall

from fastapi import FastAPI
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import CONTACTS_PAGE
from cache import cache_request


contacts_app = FastAPI()


@contacts_app.get('/')
@cache_request()
async def get_contacts():
    client = ClientSession()
    result = []

    async with client.get(CONTACTS_PAGE) as resp:
        page_data = BeautifulSoup(await resp.text(), features='html5lib')
        can_parse = False
        for tr in page_data.find('table', {'style': 'width:100%'}).find_all('tr'):
            if tr.td is not None and 'СТРУКТУРНЫЕ' in tr.td.text:
                can_parse = True
                continue
            if tr.td is not None and tr.td.text.strip() == '':
                can_parse = False
                continue
            if can_parse:
                address_info = (
                    tr.select('td:nth-child(4)')[0].encode_contents()
                    .decode('utf-8').replace('<br/>', '\n').strip()
                )
                phones = findall(r'(\d *\(\d+\) *\d-\d\d-\d\d)', address_info)
                for i in findall(r'(\d *\(\d+\) *\d-\d\d-\d\d)( */ *доб\. *(\d+))', address_info):
                    phones.append(f'доб. {i[2]}')
                    address_info = address_info.replace(i[1], '')
                for p in phones:
                    address_info = address_info.replace(p, '')
                result.append({
                    'full_name': tr.select('td:nth-child(2)')[0].text.strip(),
                    'post': tr.select('td:nth-child(3)')[0].text.strip(),
                    'phones': phones,
                    'address': address_info,
                    'email': tr.select('td:nth-child(6)')[0].text.strip(),
                })
    await client.close()
    return result
