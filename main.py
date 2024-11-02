from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from mounts.user import user_app
from mounts.branches import branches_app
from mounts.teachers import teacher_app
from mounts.blogs import blogs_app
from mounts.timetable import timetable_app
from mounts.media import media_app
from mounts.news import news_app
from mounts.courses import courses_app
from mounts.messages import messages_app
from mounts.notifications import notifications_app
from mounts.photos import photos_app
from mounts.contacts import contacts_app
from middleware.file_size_limit import LimitUploadSize
from middleware.error_handler import catch_exceptions_middleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_headers="*",
    allow_methods="*",
    allow_origins="*",
    allow_credentials=True
)
app.add_middleware(LimitUploadSize, max_upload_size=1024 * 1024 * 3)  # 3 Mb
app.middleware('http')(catch_exceptions_middleware)

app.mount('/user', user_app)
app.mount('/news', news_app)
app.mount('/courses', courses_app)
app.mount('/branches', branches_app)
app.mount('/teachers', teacher_app)
app.mount('/blogs', blogs_app)
app.mount('/timetable', timetable_app)
app.mount('/messages', messages_app)
app.mount('/media', media_app)
app.mount('/photos', photos_app)
app.mount('/contacts', contacts_app)
app.mount('/notifications', notifications_app)
