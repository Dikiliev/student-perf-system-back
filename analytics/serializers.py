from rest_framework import serializers

from analytics.models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    group_name = serializers.CharField(source="student.group.name", read_only=True)

    class Meta:
        model = Prediction
        fields = [
            "id",
            "student",
            "student_name",
            "group_name",
            "risk_score",
            "risk_level",
            "average_grade",
            "attendance_percent",
            "missed_count",
            "debt_count",
            "factors",
            "recommendations",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_student_name(self, obj):
        return obj.student.full_name