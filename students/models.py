from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Активен"
    ACADEMIC_LEAVE = "academic_leave", "Академический отпуск"
    GRADUATED = "graduated", "Выпустился"
    EXPELLED = "expelled", "Отчислен"


class GradeType(models.TextChoices):
    QUIZ = "quiz", "Тест"
    HOMEWORK = "homework", "Домашняя работа"
    MIDTERM = "midterm", "Рубежный контроль"
    EXAM = "exam", "Экзамен"
    COURSEWORK = "coursework", "Курсовая"


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Присутствовал"
    ABSENT = "absent", "Отсутствовал"
    LATE = "late", "Опоздал"
    EXCUSED = "excused", "Уважительная причина"


class Group(models.Model):
    name = models.CharField("Название группы", max_length=100, unique=True)
    course = models.PositiveSmallIntegerField("Курс", default=1)
    curator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="curated_groups",
        verbose_name="Куратор",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField("Название дисциплины", max_length=255, unique=True)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"

    def __str__(self):
        return self.name


class Student(models.Model):
    last_name = models.CharField("Фамилия", max_length=100)
    first_name = models.CharField("Имя", max_length=100)
    middle_name = models.CharField("Отчество", max_length=100, blank=True)
    record_book_number = models.CharField("Номер зачетной книжки", max_length=50, unique=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name="Группа",
    )
    email = models.EmailField("Email", blank=True)
    enrollment_year = models.PositiveSmallIntegerField("Год поступления")
    status = models.CharField(
        "Статус",
        max_length=30,
        choices=StudentStatus.choices,
        default=StudentStatus.ACTIVE,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "middle_name"]
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part).strip()


class Grade(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Студент",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Дисциплина",
    )
    value = models.PositiveSmallIntegerField(
        "Оценка",
        validators=[MinValueValidator(2), MaxValueValidator(5)],
    )
    grade_type = models.CharField(
        "Тип оценки",
        max_length=30,
        choices=GradeType.choices,
        default=GradeType.QUIZ,
    )
    comment = models.TextField("Комментарий", blank=True)
    graded_at = models.DateField("Дата выставления")

    class Meta:
        ordering = ["-graded_at", "-id"]
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name}: {self.value}"


class Attendance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Студент",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Дисциплина",
    )
    lesson_date = models.DateField("Дата занятия")
    status = models.CharField(
        "Статус посещения",
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    comment = models.TextField("Комментарий", blank=True)

    class Meta:
        ordering = ["-lesson_date", "-id"]
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject", "lesson_date"],
                name="unique_student_subject_lesson_date",
            )
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} - {self.lesson_date}"