import unittest

from mounts.timetable import (
    get_timetable_by_group_id,
    get_timetable_by_group_id_week,
    get_courses_by_branch_id,
    get_free_classrooms
)


class TimetableTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_timetable_by_group_id(self):
        timetable = await get_timetable_by_group_id(branch_id=1, group_id=264)

        assert timetable['header'] == 'Расписание для группы РП.09.21.1'
        assert 'days' in timetable and isinstance(timetable['days'], list)

    async def test_get_timetable_by_group_id_week(self):
        timetable = await get_timetable_by_group_id_week(branch_id=1, group_id=264, week=12)

        assert timetable['header'] == 'Расписание для группы РП.09.21.1'
        assert 'days' in timetable and isinstance(timetable['days'], list)

        assert len(timetable['days']) > 0
        assert len(timetable['days'][0]['lessons']) > 0
        print('\nFirst lesson on monday:', timetable['days'][0]['lessons'][0])
    
    async def test_get_courses_by_branch_id(self):
        courses = await get_courses_by_branch_id(branch_id=1)
        assert len(courses) > 0
    
    async def test_get_free_classrooms(self):
        classrooms = await get_free_classrooms()
        assert isinstance(classrooms, list)
