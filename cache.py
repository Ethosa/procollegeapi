from fastapi import FastAPI, Request
from functools import wraps
from hashlib import sha256
from typing import Callable
from time import time


class UsersCache:
    data: dict = {}


class FuncCache:
    data: dict = {}


class PhotoCache:
    albums_last_update: int = 0
    albums: list = []
    albums_full: dict = {}
    cache_time_secs: float = 60 * 60 * 24  # 24 hours


class Classrooms:
    branches = {}
    courses = {}
    classrooms = []
    exclude = ['???', 'н/к', 'дот', 'ДОТ']


def cache_request(expires: int = 60 * 60 * 10):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key_data = (func.__name__, args, frozenset(kwargs.items()))
            key = sha256(str(key_data).encode()).hexdigest()

            current_time = time()
            if key in FuncCache.data:
                cached_value, timestamp = FuncCache.data[key]
                if current_time - timestamp < expires:
                    return cached_value

            result = await func(*args, **kwargs)
            FuncCache.data[key] = (result, current_time)
            return result

        return wrapper
    return decorator
