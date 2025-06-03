from re import compile, IGNORECASE
from pathlib import Path
from datetime import timedelta

LOGIN_URL = "https://pro.kansk-tc.ru/login/index.php"
MY_DESKTOP = "https://pro.kansk-tc.ru/my/"
SERVICE = "https://pro.kansk-tc.ru/lib/ajax/service.php"
TEACHERS_TIMETABLE = "https://pro.kansk-tc.ru/blocks/manage_groups/timetable_new/print_tt_teacher.php"
STUDENTS_TIMETABLE_GROUPS = "https://pro.kansk-tc.ru/blocks/manage_groups/website/list.php"
STUDENTS_TIMETABLE_GROUP = "https://pro.kansk-tc.ru/blocks/manage_groups/website/view.php"
PROFILE_TIMETABLE = "https://pro.kansk-tc.ru/blocks/psm_desktop/desktop_lib.php?dirroot=/www/procollege"
BLOG_PAGE = "https://pro.kansk-tc.ru/blog/index.php"
PROFILE_PAGE = "https://pro.kansk-tc.ru/user/profile.php"
UPLOAD_TO_REPOSITORY = "https://pro.kansk-tc.ru/repository/repository_ajax.php?action=upload"
MAIN_WEBSITE = "http://www.kansk-tc.ru"
MAIN_WEBSITE_ALL_NEWS = "http://www.kansk-tc.ru/novosti/"
PUBLISH_BLOG_POST = "https://pro.kansk-tc.ru/blog/edit.php"
ATTACH_FILES_TO_BLOG = "https://pro.kansk-tc.ru/repository/draftfiles_ajax.php?action=list"
COURSES_PAGE = "https://pro.kansk-tc.ru/course/index.php"
NOTIFICATIONS_PAGE = "https://pro.kansk-tc.ru/message/output/popup/notifications.php"
GET_NOTIFICATIONS_PAGE = "https://pro.kansk-tc.ru/lib/ajax/service.php"
GALLERY_PAGE = "http://www.kansk-tc.ru/zhizn_kolledzha/fotogalereya"
CONTACTS_PAGE = "http://www.kansk-tc.ru/o_kolledzhe/o_strukture_i_ob_organah_upravleniya_kolledzha"
VIEW_PAGE = "https://pro.kansk-tc.ru/course/view.php"

BLOG_POST_EDIT = "https://pro.kansk-tc.ru/blog/edit.php"
DELETE_BLOG_POST = "https://pro.kansk-tc.ru/blog/edit.php?action=delete&entryid="


CORE_MESSAGE_GET_CONVERSATIONS = 'core_message_get_conversations'
CORE_MESSAGE_GET_CONVERSATION_MESSAGES = 'core_message_get_conversation_messages'
CORE_MESSAGE_SEND_MESSAGES_TO_CONVERSATION = 'core_message_send_messages_to_conversation'
MESSAGE_POPUP_GET_POPUP_NOTIFICATIONS = "message_popup_get_popup_notifications"


API_URL = "http://localhost:8000"


CACHE_DIR = Path('./cache')
CACHE_DIR.mkdir(exist_ok=True)
CACHE_LIFETIME = timedelta(hours=24)


BAD_WORDS = compile(
    (
        r'\b(bitch|sex|gay|gays|bitches|anal|fuck)\b'
    ),
    IGNORECASE
)


USER_AGENT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/134.0.0.0 YaBrowser/25.4.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
        '*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    ),
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'ru,en;q=0.9,la;q=0.8,af;q=0.7,de;q=0.6,ko;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded',
}
