from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from analytics.models import Prediction
from analytics.serializers import PredictionSerializer


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "message": "API is working",
            }
        )


class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prediction.objects.select_related("student", "student__group", "created_by").all()
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        group_id = self.request.query_params.get("group")
        risk_level = self.request.query_params.get("risk_level")

        if group_id:
            queryset = queryset.filter(student__group_id=group_id)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)

        return queryset