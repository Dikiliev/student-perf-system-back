from rest_framework import serializers

from students.models import Attendance, Grade, Group, Student, Subject


class GroupSerializer(serializers.ModelSerializer):
    curator_username = serializers.CharField(source="curator.username", read_only=True)
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "course",
            "curator",
            "curator_username",
            "students_count",
            "created_at",
        ]

    def get_students_count(self, obj):
        return obj.students.count()


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "description", "created_at"]


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    group_name = serializers.CharField(source="group.name", read_only=True)
    current_risk_level = serializers.SerializerMethodField()
    current_risk_score = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "last_name",
            "first_name",
            "middle_name",
            "full_name",
            "record_book_number",
            "group",
            "group_name",
            "email",
            "enrollment_year",
            "status",
            "current_risk_level",
            "current_risk_score",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        return obj.full_name

    def get_current_risk_level(self, obj):
        prediction = getattr(obj, "prediction", None)
        return prediction.risk_level if prediction else None

    def get_current_risk_score(self, obj):
        prediction = getattr(obj, "prediction", None)
        return prediction.risk_score if prediction else None


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id",
            "student",
            "student_name",
            "subject",
            "subject_name",
            "value",
            "grade_type",
            "comment",
            "graded_at",
        ]

    def get_student_name(self, obj):
        return obj.student.full_name


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "subject",
            "subject_name",
            "lesson_date",
            "status",
            "comment",
        ]

    def get_student_name(self, obj):
        return obj.student.full_name