from datetime import date, timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analytics.models import Prediction
from analytics.services import upsert_prediction_for_student
from students.models import (
    Attendance,
    AttendanceStatus,
    Grade,
    GradeType,
    Group,
    Student,
    Subject,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Заполняет базу демонстрационными данными для дипломного проекта"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Очистить существующие учебные данные и заполнить заново",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options["reset"]

        if Student.objects.exists() and not reset:
            raise CommandError(
                "В базе уже есть студенты. Запусти команду с --reset, если хочешь пересоздать demo-данные."
            )

        if reset:
            self.stdout.write("Удаляю старые demo-данные...")
            Prediction.objects.all().delete()
            Attendance.objects.all().delete()
            Grade.objects.all().delete()
            Student.objects.all().delete()
            Group.objects.all().delete()
            Subject.objects.all().delete()

        self.stdout.write("Создаю пользователей...")
        users = self._create_users()

        self.stdout.write("Создаю группы...")
        groups = self._create_groups(users)

        self.stdout.write("Создаю дисциплины...")
        subjects = self._create_subjects()

        self.stdout.write("Создаю студентов...")
        students = self._create_students(groups)

        self.stdout.write("Создаю оценки и посещаемость...")
        self._create_academic_data(students, subjects)

        self.stdout.write("Пересчитываю прогнозы...")
        for student in students:
            upsert_prediction_for_student(student, created_by=users["teacher"])

        self.stdout.write(self.style.SUCCESS("Demo-данные успешно созданы."))

    def _create_users(self):
        users_config = [
            {
                "username": "admin",
                "email": "admin_demo@example.com",
                "password": "estaesta!",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "System",
                "last_name": "Admin",
            },
            {
                "username": "teacher_demo",
                "email": "teacher_demo@example.com",
                "password": "Teacher12345!",
                "role": "teacher",
                "is_staff": True,
                "is_superuser": False,
                "first_name": "Ирина",
                "last_name": "Петрова",
            },
            {
                "username": "curator_demo",
                "email": "curator_demo@example.com",
                "password": "Curator12345!",
                "role": "curator",
                "is_staff": True,
                "is_superuser": False,
                "first_name": "Аслан",
                "last_name": "Исаев",
            },
        ]

        result = {}

        for item in users_config:
            user, created = User.objects.get_or_create(
                username=item["username"],
                defaults={
                    "email": item["email"],
                    "role": item["role"],
                    "is_staff": item["is_staff"],
                    "is_superuser": item["is_superuser"],
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                },
            )

            if created:
                user.set_password(item["password"])
                user.save()
            else:
                changed = False
                if user.email != item["email"]:
                    user.email = item["email"]
                    changed = True
                if getattr(user, "role", None) != item["role"]:
                    user.role = item["role"]
                    changed = True
                if user.is_staff != item["is_staff"]:
                    user.is_staff = item["is_staff"]
                    changed = True
                if user.is_superuser != item["is_superuser"]:
                    user.is_superuser = item["is_superuser"]
                    changed = True
                if user.first_name != item["first_name"]:
                    user.first_name = item["first_name"]
                    changed = True
                if user.last_name != item["last_name"]:
                    user.last_name = item["last_name"]
                    changed = True

                user.set_password(item["password"])
                changed = True

                if changed:
                    user.save()

            result[item["role"]] = user

        return result

    def _create_groups(self, users):
        groups = [
            Group.objects.create(name="ИС-101", course=1, curator=users["curator"]),
            Group.objects.create(name="ИС-102", course=1, curator=users["curator"]),
            Group.objects.create(name="ПИ-201", course=2, curator=users["teacher"]),
        ]
        return groups

    def _create_subjects(self):
        subject_names = [
            "Математика",
            "Программирование",
            "Базы данных",
            "Английский язык",
            "Статистика",
        ]
        return [Subject.objects.create(name=name) for name in subject_names]

    def _create_students(self, groups):
        students_data = [
            ("Иванов", "Илья", "Сергеевич", groups[0], "RB-1001"),
            ("Петров", "Артур", "Магомедович", groups[0], "RB-1002"),
            ("Сидорова", "Анна", "Олеговна", groups[0], "RB-1003"),
            ("Гадаев", "Тимур", "Русланович", groups[0], "RB-1004"),

            ("Алиева", "Марина", "Игоревна", groups[1], "RB-1005"),
            ("Юсупов", "Адам", "Султанович", groups[1], "RB-1006"),
            ("Казбекова", "Лина", "Ахмедовна", groups[1], "RB-1007"),
            ("Мусаев", "Рамзан", "Идрисович", groups[1], "RB-1008"),

            ("Васильев", "Денис", "Павлович", groups[2], "RB-1009"),
            ("Гереева", "Диана", "Шамилевна", groups[2], "RB-1010"),
            ("Ахмадов", "Саид", "Исламович", groups[2], "RB-1011"),
            ("Борисова", "Екатерина", "Андреевна", groups[2], "RB-1012"),
        ]

        students = []
        for idx, (last_name, first_name, middle_name, group, record_book) in enumerate(students_data, start=1):
            student = Student.objects.create(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                record_book_number=record_book,
                group=group,
                email=f"student{idx}@example.com",
                enrollment_year=2024 if group.course == 1 else 2023,
                status="active",
            )
            students.append(student)

        return students

    def _create_academic_data(self, students, subjects):
        random.seed(42)
        today = date.today()

        high_risk_students = students[:4]
        medium_risk_students = students[4:8]
        low_risk_students = students[8:]

        for student in students:
            if student in high_risk_students:
                grade_pool = [2, 2, 3, 3, 3, 4]
                absent_chance = 0.45
                late_chance = 0.10
            elif student in medium_risk_students:
                grade_pool = [3, 3, 4, 4, 4, 5]
                absent_chance = 0.20
                late_chance = 0.10
            else:
                grade_pool = [4, 4, 5, 5, 5]
                absent_chance = 0.05
                late_chance = 0.10

            for subject in subjects:
                grade_types = [GradeType.QUIZ, GradeType.HOMEWORK, GradeType.EXAM]
                for j, grade_type in enumerate(grade_types):
                    grade_value = random.choice(grade_pool)

                    Grade.objects.create(
                        student=student,
                        subject=subject,
                        value=grade_value,
                        grade_type=grade_type,
                        comment="Demo оценка",
                        graded_at=today - timedelta(days=20 - j * 5),
                    )

                for k in range(8):
                    lesson_date = today - timedelta(days=(k + 1) * 7)

                    roll = random.random()
                    if roll < absent_chance:
                        status = AttendanceStatus.ABSENT
                    elif roll < absent_chance + late_chance:
                        status = AttendanceStatus.LATE
                    else:
                        status = AttendanceStatus.PRESENT

                    Attendance.objects.create(
                        student=student,
                        subject=subject,
                        lesson_date=lesson_date,
                        status=status,
                        comment="Demo посещаемость",
                    )