from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse

from .serializers import FileUploadSerializer
from .importers.group_importer import GroupImporter
from .importers.subject_importer import SubjectImporter
from .importers.student_importer import StudentImporter
from .importers.grade_importer import GradeImporter
from .importers.attendance_importer import AttendanceImporter
from .exporters.base import ExporterService
from .services.predictions import trigger_prediction_recalculation

# Models for export
from students.models import Group, Subject, Student, Grade, Attendance
from analytics.models import Prediction

ENTITY_MAP = {
    "groups": {
        "importer": GroupImporter,
        "model": Group,
        "export_headers": ["name", "course", "curator__username"],
        "template_headers": ["name", "course", "curator_username"]
    },
    "subjects": {
        "importer": SubjectImporter,
        "model": Subject,
        "export_headers": ["name", "description"],
        "template_headers": ["name", "description"]
    },
    "students": {
        "importer": StudentImporter,
        "model": Student,
        "export_headers": ["record_book_number", "last_name", "first_name", "middle_name", "email", "group__name", "enrollment_year", "status"],
        "template_headers": ["record_book_number", "last_name", "first_name", "middle_name", "email", "group_name", "enrollment_year", "status"]
    },
    "grades": {
        "importer": GradeImporter,
        "model": Grade,
        "export_headers": ["student__record_book_number", "subject__name", "value", "grade_type", "graded_at", "comment"],
        "template_headers": ["student_record_book_number", "subject_name", "value", "grade_type", "graded_at", "comment"]
    },
    "attendance": {
        "importer": AttendanceImporter,
        "model": Attendance,
        "export_headers": ["student__record_book_number", "subject__name", "lesson_date", "status", "comment"],
        "template_headers": ["student_record_book_number", "subject_name", "lesson_date", "status", "comment"]
    },
    "predictions": {
        "importer": None, # Read Only
        "model": Prediction,
        "export_headers": ["student__record_book_number", "student__last_name", "risk_level", "risk_score", "average_grade", "attendance_percent"],
        "template_headers": []
    }
}

class TemplateDownloadView(APIView):
    def get(self, request, entity):
        if entity not in ENTITY_MAP or not ENTITY_MAP[entity]["template_headers"]:
            return Response({"error": "Invalid entity"}, status=status.HTTP_400_BAD_REQUEST)
            
        fmt = request.query_params.get("format", "csv").lower()
        headers = ENTITY_MAP[entity]["template_headers"]
        
        if fmt == "csv":
            content = ExporterService.export_to_csv([], headers=headers)
            content_type = "text/csv"
            ext = "csv"
        elif fmt == "xlsx":
            content = ExporterService.export_to_xlsx([], headers=headers, sheet_name=entity.title())
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:
            return Response({"error": "Invalid format"}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="template_{entity}.{ext}"'
        return response


class ExportView(APIView):
    def get(self, request, entity):
        if entity not in ENTITY_MAP:
            return Response({"error": "Invalid entity"}, status=status.HTTP_400_BAD_REQUEST)
            
        fmt = request.query_params.get("format", "csv").lower()
        model = ENTITY_MAP[entity]["model"]
        headers = ENTITY_MAP[entity]["export_headers"]
        
        # Flatten relations for export using values()
        queryset = model.objects.all().values(*headers)
        data = list(queryset)
        
        # Map output headers to template headers for consistency
        if ENTITY_MAP[entity]["template_headers"]:
            header_mapping = dict(zip(headers, ENTITY_MAP[entity]["template_headers"]))
            mapped_data = []
            for row in data:
                mapped_data.append({header_mapping.get(k, k): v for k, v in row.items()})
            data = mapped_data
            output_headers = ENTITY_MAP[entity]["template_headers"]
        else:
            output_headers = headers

        if fmt == "csv":
            content = ExporterService.export_to_csv(data, headers=output_headers)
            content_type = "text/csv"
            ext = "csv"
        elif fmt == "xlsx":
            content = ExporterService.export_to_xlsx(data, headers=output_headers, sheet_name=entity.title())
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:
            return Response({"error": "Invalid format"}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="export_{entity}.{ext}"'
        return response


class ImportPreviewView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, entity):
        if entity not in ENTITY_MAP or not ENTITY_MAP[entity]["importer"]:
            return Response({"error": "Invalid entity for import"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data["file"]
        mode = serializer.validated_data["mode"]
        
        file_ext = file_obj.name.split('.')[-1].lower()
        if file_ext not in ["csv", "xlsx"]:
            return Response({"error": "Only CSV and XLSX files are supported."}, status=status.HTTP_400_BAD_REQUEST)

        importer_class = ENTITY_MAP[entity]["importer"]
        importer = importer_class(file_obj=file_obj, file_format=file_ext, mode=mode)
        
        try:
            summary = importer.validate()
            # Store instance in session/cache for commit if needed, or rely on stateless re-upload
            # For this architecture, stateless re-upload on commit is safer and cleaner without celery.
            return Response(summary, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ImportCommitView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, entity):
        if entity not in ENTITY_MAP or not ENTITY_MAP[entity]["importer"]:
            return Response({"error": "Invalid entity for import"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data["file"]
        mode = serializer.validated_data["mode"]
        file_ext = file_obj.name.split('.')[-1].lower()
        
        importer_class = ENTITY_MAP[entity]["importer"]
        importer = importer_class(file_obj=file_obj, file_format=file_ext, mode=mode)
        
        try:
            # Re-validate since we are stateless
            summary = importer.validate()
            if importer.invalid_rows > 0:
                summary.update({"error": "File contains validation errors, commit partially aborted."})
                return Response(summary, status=status.HTTP_400_BAD_REQUEST)
                
            summary = importer.commit()
            
            # Hook into Predictions
            if entity in ["grades", "attendance"] and summary.get("valid_rows", 0) > 0:
                # Find distinct student IDs impacted
                student_ids = list(set([row["student"].id for row in importer.valid_data_rows]))
                trigger_prediction_recalculation(student_ids)
                summary["predictions_recalculated"] = len(student_ids)

            return Response(summary, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
