from re import match, M

from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from constants import USER_AGENT_HEADERS, MY_DESKTOP


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


def beautify_src(link: str, root: str):
    if not match(r'^https?://', link, M):
        return root + link
    return link
