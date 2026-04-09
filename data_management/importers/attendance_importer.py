from typing import Dict, Any, Tuple, List
import pandas as pd
from students.models import Attendance, Student, Subject
from .base import ImporterService

class AttendanceImporter(ImporterService):
    EXPECTED_COLUMNS = [
        "student_record_book_number", "subject_name", 
        "lesson_date", "status", "comment"
    ]

    def validate_row(self, row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any], List[Dict], List[Dict]]:
        errors = []
        warnings = []
        is_valid = True
        
        rbn = str(row.get("student_record_book_number") or "").strip()
        subject_name = row.get("subject_name")
        status = row.get("status")
        lesson_date_raw = row.get("lesson_date")
        comment = row.get("comment") or ""

        student = None
        if not rbn:
            errors.append({"row": row_num, "field": "student_record_book_number", "message": "Required."})
            is_valid = False
        else:
            try:
                student = Student.objects.get(record_book_number=rbn)
            except Student.DoesNotExist:
                errors.append({"row": row_num, "field": "student_record_book_number", "message": f"Student '{rbn}' not found."})
                is_valid = False

        subject = None
        if not subject_name:
            errors.append({"row": row_num, "field": "subject_name", "message": "Required."})
            is_valid = False
        else:
            try:
                subject = Subject.objects.get(name=subject_name)
            except Subject.DoesNotExist:
                errors.append({"row": row_num, "field": "subject_name", "message": f"Subject '{subject_name}' not found."})
                is_valid = False

        # Validate status enum
        valid_statuses = [c[0] for c in Attendance.AttendanceStatusChoices.choices]
        if status not in valid_statuses:
            errors.append({"row": row_num, "field": "status", "message": f"Invalid status. Must be in {valid_statuses}."})
            is_valid = False

        # Validate lesson_date
        lesson_date = None
        if not lesson_date_raw or pd.isna(lesson_date_raw):
            errors.append({"row": row_num, "field": "lesson_date", "message": "Required (format YYYY-MM-DD)."})
            is_valid = False
        else:
            try:
                lesson_date = pd.to_datetime(lesson_date_raw).date()
            except Exception:
                errors.append({"row": row_num, "field": "lesson_date", "message": "Invalid date format."})
                is_valid = False
        
        action = "create"
        attendance = None
        if is_valid:
            try:
                attendance = Attendance.objects.get(
                    student=student,
                    subject=subject,
                    lesson_date=lesson_date
                )
                action = "update"
            except Attendance.DoesNotExist:
                action = "create"
            except Attendance.MultipleObjectsReturned:
                action = "update"
                attendance = Attendance.objects.filter(
                    student=student, subject=subject, lesson_date=lesson_date
                ).first()
                warnings.append({"row": row_num, "message": "Multiple identical records found, updating the first one."})

            if self.mode == "create_only" and action == "update":
                warnings.append({"row": row_num, "message": "Record already exists. Skipping."})
                action = "skip"
                is_valid = False
            elif self.mode == "update_only" and action == "create":
                warnings.append({"row": row_num, "message": "Record not found. Skipping."})
                action = "skip"
                is_valid = False
                
        mapped_data = {}
        if is_valid and action != "skip":
            mapped_data = {
                "student": student,
                "subject": subject,
                "lesson_date": lesson_date,
                "status": status,
                "comment": comment
            }
            if attendance:
                mapped_data["instance"] = attendance
                
        return (is_valid, action, mapped_data, errors, warnings)

    def commit_rows(self, rows_data: List[Dict[str, Any]]):
        for data in rows_data:
            instance = data.get("instance")
            
            if instance:
                instance.status = data["status"]
                instance.comment = data["comment"]
                instance.save()
            else:
                Attendance.objects.create(
                    student=data["student"],
                    subject=data["subject"],
                    lesson_date=data["lesson_date"],
                    status=data["status"],
                    comment=data["comment"],
                )
