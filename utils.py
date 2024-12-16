from re import match, M, findall
from urllib.parse import quote_plus

from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup, PageElement, NavigableString

from constants import USER_AGENT_HEADERS, MY_DESKTOP, MAIN_WEBSITE, BAD_WORDS
from cache import Classrooms
from env import API_URL


def error(message: str, status_code: int = 400) -> JSONResponse:
    """
    Создает словарь ошибки. Используется для сообщений об ошибках

    :param message: информация об ошибке
    :param status_code:  HTTP статус
    """
    return JSONResponse({'error': message, 'code': status_code}, status_code=status_code)


def headers(data: dict | None = None) -> dict:
    """
    Собираем стандартный набор заголовков в виде dict

    :param data: Дополнительные заголовки
    """
    result = USER_AGENT_HEADERS
    if data is None:
        return result
    for key in data.keys():
        result[key] = data[key]
    return result


def get_moodle(access_token: str) -> str:
    """
    Собирает MoodleSession из access_token
    """
    data = access_token.split(':')
    return {
        'key': 'MoodleSession' + data[0],
        'value': data[1],
        'cookie': 'MoodleSession' + data[0] + '=' + data[1]
    }


async def check_auth(access_token) -> JSONResponse | dict:
    """
    Проверяет валидность токена
    """
    if not access_token:
        return error('Вы не авторизованы')
    if ':' not in access_token:
        return error('Токен неправильный')
    moodle = get_moodle(access_token)
    _headers = headers({
        'Cookie': moodle['cookie']
    })
    async with ClientSession() as session:
        async with session.get(MY_DESKTOP, headers=_headers) as response:
            page_data = BeautifulSoup(await response.text())
            if page_data.find('div', id='nav-notification-popover-container') is None:
                _headers = error("Истек срок действия вашего токена", 401)
    return _headers


def match_bad_words(string: str) -> bool:
    result = findall(BAD_WORDS, string)
    for i in result:
        if i:
            return True
    return False


def to_query_param(key: str, val: list[str] | str) -> str:
    if isinstance(val, list):
        new_key = quote_plus(f'{key}[]')
        return '&'.join([
            new_key + '=' + quote_plus(i)
            for i in val
        ])
    return quote_plus(key) + '=' + quote_plus(val)


def x_form_urlencoded(data: dict) -> str:
    return '&'.join([
        to_query_param(i, data[i])
        for i in data.keys()
    ])


def beautify_src(link: str, root: str):
    if not match(r'^https?://', link, M):
        return root + link
    return link


def proxify(link: str, access_token: str | None = None):
    if access_token:
        return f'{API_URL}/media/proxy/file?access_token={access_token}&link={link}'
    return f'{API_URL}/media/proxy/file?link={link}'


def _clean_attributes(html: PageElement, access_token: str | None = None):
    if isinstance(html, NavigableString):
        return
    html['style'] = ''
    html['class'] = ''
    del html['style']
    del html['class']
    if html.get('href'):
        if html['href'].startswith('/'):
            html['href'] = f'{MAIN_WEBSITE}{html["href"]}'
        html['href'] = html['href'].replace(' ', '%20')
        if html.name == 'a':
            html['target'] = '_blank'
    if html.get('src'):
        if html.name in ['img'] and html['src'].startswith('/'):
            html['src'] = f'{MAIN_WEBSITE}{html["src"]}'.replace(' ', '%20')
        html['src'] = html['src'].replace(' ', '%20')
        html['src'] = proxify(html['src'], access_token)
    for i in html.children:
        _clean_attributes(i, access_token)


def clean_styles(html: PageElement, access_token: str | None = None) -> PageElement:
    _clean_attributes(html, access_token)
    return html


def lessons_length(day: dict):
    if 'lessons' not in day:
        return
    if len(day['lessons']) == 0:
        day['hours'] = 0
        day['start'] = ''
        day['end'] = ''
        return
    minutes = 0
    for lesson in day['lessons']:
        start_hours, start_minutes = lesson['start'].split(':')
        end_hours, end_minutes = lesson['end'].split(':')
        start = int(start_hours)*60 + int(start_minutes)
        end = int(end_hours)*60 + int(end_minutes)
        minutes += end - start
    day['hours'] = round(minutes / 60)
    day['start'] = day['lessons'][0]['start']
    day['end'] = day['lessons'][-1]['end']
