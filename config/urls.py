from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from analytics.views import HealthCheckView, PredictionViewSet
from students.views import (
    AttendanceViewSet,
    GradeViewSet,
    GroupViewSet,
    StudentViewSet,
    SubjectViewSet,
)
from users.views import CustomTokenObtainPairView, MeView

router = DefaultRouter()
router.register("groups", GroupViewSet, basename="group")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("students", StudentViewSet, basename="student")
router.register("grades", GradeViewSet, basename="grade")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("predictions", PredictionViewSet, basename="prediction")

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/health/", HealthCheckView.as_view(), name="health-check"),

    path("api/auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/auth/me/", MeView.as_view(), name="auth_me"),

    path("api-auth/", include("rest_framework.urls")),
    path("api/data/", include("data_management.urls")),
    path("api/", include(router.urls)),
]