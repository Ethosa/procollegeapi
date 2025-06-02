import unittest

from mounts.teachers import (
    get_teachers_by_branch_id,
    get_teacher_week_by_id
)


class TeachersTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_teachers_by_branch_id(self):
        teachers = await get_teachers_by_branch_id(branch_id=1)
        
        assert isinstance(teachers, list) and len(teachers) > 0
        print('\nFirst teacher in the list:', teachers[0])

    async def test_get_teacher_week_by_id(self):
        teachers = await get_teachers_by_branch_id(branch_id=1)
        timetable = await get_teacher_week_by_id(branch_id=1, teacher_id=teachers[0]['id'])

        assert len(timetable['days']) == 7
        assert timetable['teacher'] == teachers[0]['title']
        print(f'\nMonday of {timetable["teacher"]}:', timetable['days'][0])
