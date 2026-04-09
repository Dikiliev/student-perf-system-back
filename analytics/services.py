from django.db.models import Avg, Count, Q

from analytics.models import Prediction, RiskLevel
from students.models import AttendanceStatus


def calculate_student_risk(student):
    average_grade = student.grades.aggregate(avg=Avg("value"))["avg"]
    debt_count = student.grades.filter(value=2).count()

    attendance_stats = student.attendances.aggregate(
        effective_total=Count("id", filter=~Q(status=AttendanceStatus.EXCUSED)),
        present_count=Count(
            "id",
            filter=Q(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
        ),
        missed_count=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
    )

    effective_total = attendance_stats["effective_total"] or 0
    present_count = attendance_stats["present_count"] or 0
    missed_count = attendance_stats["missed_count"] or 0

    attendance_percent = None
    if effective_total > 0:
        attendance_percent = round((present_count / effective_total) * 100, 2)

    score = 0
    factors = []
    recommendations = []

    if average_grade is None and effective_total == 0:
        factors.append("Недостаточно данных для точного прогноза")
        recommendations.append("Заполните данные об оценках и посещаемости")
    else:
        if average_grade is not None:
            average_grade = round(float(average_grade), 2)

            if average_grade < 3.0:
                score += 35
                factors.append("Очень низкий средний балл")
                recommendations.append("Назначить индивидуальную консультацию")
            elif average_grade < 3.5:
                score += 20
                factors.append("Низкий средний балл")
                recommendations.append("Усилить контроль текущей успеваемости")
            elif average_grade < 4.0:
                score += 10
                factors.append("Средний балл ниже желаемого уровня")
                recommendations.append("Рекомендовать дополнительные занятия")

        if attendance_percent is not None:
            if attendance_percent < 60:
                score += 30
                factors.append("Критически низкая посещаемость")
                recommendations.append("Провести беседу о посещаемости")
            elif attendance_percent < 75:
                score += 20
                factors.append("Низкая посещаемость")
                recommendations.append("Усилить контроль присутствия на занятиях")
            elif attendance_percent < 85:
                score += 10
                factors.append("Посещаемость ниже целевого уровня")
                recommendations.append("Отслеживать динамику посещаемости")

        if missed_count >= 10:
            score += 15
            factors.append("Большое количество пропусков")
            recommendations.append("Проверить причины пропусков")
        elif missed_count >= 5:
            score += 8
            factors.append("Имеются регулярные пропуски")
            recommendations.append("Попросить студента сократить пропуски")

        if debt_count >= 3:
            score += 25
            factors.append("Несколько академических задолженностей")
            recommendations.append("Составить план ликвидации долгов")
        elif debt_count >= 1:
            score += 15
            factors.append("Есть академическая задолженность")
            recommendations.append("Назначить сроки закрытия задолженности")

    recommendations = list(dict.fromkeys(recommendations))

    if score >= 60:
        risk_level = RiskLevel.HIGH
    elif score >= 30:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "average_grade": average_grade,
        "attendance_percent": attendance_percent,
        "missed_count": missed_count,
        "debt_count": debt_count,
        "factors": factors,
        "recommendations": recommendations,
    }


def upsert_prediction_for_student(student, created_by=None):
    data = calculate_student_risk(student)

    prediction, _ = Prediction.objects.update_or_create(
        student=student,
        defaults={
            **data,
            "created_by": created_by,
        },
    )
    return prediction