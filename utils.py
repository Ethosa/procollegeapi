from fastapi.responses import JSONResponse

from api import USER_AGENT_HEADERS


def error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({'error': message, 'code': status_code}, status_code=status_code)


def headers(data: dict | None = None) -> dict:
    result = USER_AGENT_HEADERS
    if data is None:
        return result
    for key in data.keys():
        result[key] = data[key]
    return result


def get_moodle(access_token: str) -> str:
    data = access_token.split(':')
    return {
        'key': 'MoodleSession' + data[0],
        'value': data[1],
        'cookie': 'MoodleSession' + data[0] + '=' + data[1]
    }
