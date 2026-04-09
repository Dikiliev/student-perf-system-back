from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Q

from analytics.serializers import PredictionSerializer
from analytics.services import upsert_prediction_for_student
from students.models import Attendance, Grade, Group, Student, Subject
from students.serializers import (
    AttendanceSerializer,
    GradeSerializer,
    GroupSerializer,
    StudentSerializer,
    SubjectSerializer,
)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.select_related("curator").all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="risk-summary")
    def risk_summary(self, request, pk=None):
        group = self.get_object()
        predictions = group.students.filter(prediction__isnull=False)

        return Response(
            {
                "group_id": group.id,
                "group_name": group.name,
                "students_count": group.students.count(),
                "predicted_students_count": predictions.count(),
                "low_risk_count": predictions.filter(prediction__risk_level="low").count(),
                "medium_risk_count": predictions.filter(prediction__risk_level="medium").count(),
                "high_risk_count": predictions.filter(prediction__risk_level="high").count(),
            }
        )


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related("group", "group__curator").all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        group_id = self.request.query_params.get("group")
        status_value = self.request.query_params.get("status")
        search = self.request.query_params.get("search")

        if group_id:
            queryset = queryset.filter(group_id=group_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if search:
            queryset = queryset.filter(
                Q(last_name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(middle_name__icontains=search)
                | Q(record_book_number__icontains=search)
            )

        return queryset

    @action(detail=True, methods=["post"], url_path="predict")
    def predict(self, request, pk=None):
        student = self.get_object()
        prediction = upsert_prediction_for_student(student, created_by=request.user)
        return Response(PredictionSerializer(prediction).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="predict-all")
    def predict_all(self, request):
        students = self.get_queryset()
        result = []

        for student in students:
            prediction = upsert_prediction_for_student(student, created_by=request.user)
            result.append(PredictionSerializer(prediction).data)

        return Response(
            {
                "message": "Прогнозы успешно пересчитаны",
                "count": len(result),
                "results": result,
            },
            status=status.HTTP_200_OK,
        )


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.select_related("student", "subject").all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get("student")
        subject_id = self.request.query_params.get("subject")

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("student", "subject").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get("student")
        subject_id = self.request.query_params.get("subject")

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset