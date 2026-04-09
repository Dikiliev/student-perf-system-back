from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from students.models import Attendance, Grade, Group, Student, Subject


@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin):
    list_display = ("id", "name", "course", "curator", "created_at")
    search_fields = ("name",)
    list_filter = ("course",)


@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "full_name",
        "record_book_number",
        "group",
        "status",
        "enrollment_year",
        "created_at",
    )
    search_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "record_book_number",
    )
    list_filter = ("group", "status", "enrollment_year")


@admin.register(Grade)
class GradeAdmin(ImportExportModelAdmin):
    list_display = ("id", "student", "subject", "value", "grade_type", "graded_at")
    search_fields = ("student__last_name", "student__first_name", "subject__name")
    list_filter = ("grade_type", "subject", "graded_at")


@admin.register(Attendance)
class AttendanceAdmin(ImportExportModelAdmin):
    list_display = ("id", "student", "subject", "lesson_date", "status")
    search_fields = ("student__last_name", "student__first_name", "subject__name")
    list_filter = ("status", "subject", "lesson_date")