from django.conf import settings
from django.db import models

from students.models import Student


class RiskLevel(models.TextChoices):
    LOW = "low", "Низкий"
    MEDIUM = "medium", "Средний"
    HIGH = "high", "Высокий"


class Prediction(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="prediction",
        verbose_name="Студент",
    )
    risk_score = models.PositiveSmallIntegerField("Балл риска", default=0)
    risk_level = models.CharField(
        "Уровень риска",
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
    )
    average_grade = models.DecimalField(
        "Средний балл",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )
    attendance_percent = models.DecimalField(
        "Посещаемость, %",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    missed_count = models.PositiveIntegerField("Количество пропусков", default=0)
    debt_count = models.PositiveIntegerField("Количество долгов", default=0)
    factors = models.JSONField("Факторы риска", default=list, blank=True)
    recommendations = models.JSONField("Рекомендации", default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_predictions",
        verbose_name="Кто рассчитал",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        verbose_name = "Прогноз"
        verbose_name_plural = "Прогнозы"

    def __str__(self):
        return f"{self.student.full_name} - {self.get_risk_level_display()} ({self.risk_score})"