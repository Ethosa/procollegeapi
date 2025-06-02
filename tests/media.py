import unittest

from mounts.media import (
    proxy_file_get
)


class MediaTest(unittest.IsolatedAsyncioTestCase):
    async def test_proxy_file_get(self):
        link = (
            'https://sun9-61.userapi.com/impg/'
            'SgBkUzjatZNniWDK_FPTZ78IM9GLJSP3V'
            'xRZ9g/RPP4vTXoQ-o.jpg?size=1748x6'
            '85&quality=95&sign=9b961d8add2354'
            '3098fbb26a9343ff8e&type=album'
        )
        image_file = await proxy_file_get(link=link)

        assert image_file is not None
