from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from mounts.user import user_app
from mounts.branches import branches_app
from mounts.teachers import teacher_app
from mounts.blogs import blogs_app
from mounts.timetable import timetable_app
from mounts.media import media_app
from middleware.file_size_limit import LimitUploadSize


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_headers="*",
    allow_methods="*",
    allow_origins="*",
    allow_credentials=True
)
app.add_middleware(LimitUploadSize, max_upload_size=1024 * 1024 * 3)  # 3 Mb

app.mount('/user', user_app)
app.mount('/branches', branches_app)
app.mount('/teachers', teacher_app)
app.mount('/blogs', blogs_app)
app.mount('/timetable', timetable_app)
app.mount('/media', media_app)
