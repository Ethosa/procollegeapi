
class UsersCache:
    data: dict = {}


class PhotoCache:
    albums_last_update: int = 0
    albums: list = []
    albums_full: dict = {}
    cache_time_secs: float = 60 * 60 * 4  # 4 hours
