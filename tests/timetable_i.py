import unittest
from random import choice

from mounts.timetable import (
    get_timetable_by_group_id,
    get_courses_by_branch_id
)
from mounts.teachers import get_teachers_by_branch_id, get_teacher_week_by_id
from mounts.branches import get_all_branches


class TimetableITest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        branches = await get_all_branches()
        self.branch_id = branches[0]['id']
        self.teachers_list = await get_teachers_by_branch_id(self.branch_id)
        self.teacher = choice(self.teachers_list)

    async def test_find_group(self):
        courses = await get_courses_by_branch_id(self.branch_id)
        timetable = await get_teacher_week_by_id(self.branch_id, self.teacher['id'])

        if len(timetable['days'][0]['lessons']) > 0:
            first_lesson_in_week = timetable['days'][0]['lessons'][0]
            number = int(first_lesson_in_week['number'])
            group_id = None
            group_lesson = None

            for course in courses:
                for group in course['groups']:
                    if group['title'] == first_lesson_in_week['group']:
                        group_id = group['id']
                        break
            if group_id is not None:
                group_timetable = await get_timetable_by_group_id(self.branch_id, group_id)
                for lesson in group_timetable['days'][0]['lessons']:
                    if int(lesson['number']) == number:
                        group_lesson = lesson
                        break
            if group_lesson is not None:
                assert first_lesson_in_week['classroom'] == group_lesson['classroom']
                assert first_lesson_in_week['number'] == group_lesson['number']
                print("\nTeacher:", self.teacher['title'])
                print("Group:", first_lesson_in_week['group'])
                print("Subject:", group_lesson['title'])
    