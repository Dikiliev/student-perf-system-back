from django.contrib import admin

from import_export.admin import ExportMixin
from analytics.models import Prediction


@admin.register(Prediction)
class PredictionAdmin(ExportMixin, admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
    list_display = (
        "id",
        "student",
        "risk_score",
        "risk_level",
        "average_grade",
        "attendance_percent",
        "debt_count",
        "updated_at",
    )
    search_fields = (
        "student__last_name",
        "student__first_name",
        "student__middle_name",
        "student__record_book_number",
    )
    list_filter = ("risk_level", "updated_at")