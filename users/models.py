from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Администратор"
    TEACHER = "teacher", "Преподаватель"
    CURATOR = "curator", "Куратор"


class User(AbstractUser):
    role = models.CharField(
        "Роль",
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.TEACHER,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"