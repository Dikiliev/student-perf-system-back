from typing import Dict, Any, Tuple, List
import pandas as pd
from students.models import Grade, Student, Subject
from .base import ImporterService

class GradeImporter(ImporterService):
    EXPECTED_COLUMNS = [
        "student_record_book_number", "subject_name", 
        "value", "grade_type", "graded_at", "comment"
    ]

    def validate_row(self, row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any], List[Dict], List[Dict]]:
        errors = []
        warnings = []
        is_valid = True
        
        rbn = str(row.get("student_record_book_number") or "").strip()
        subject_name = row.get("subject_name")
        value = row.get("value")
        grade_type = row.get("grade_type") or "homework"
        graded_at_raw = row.get("graded_at")
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
                
        # Validate value
        if value is None or pd.isna(value):
            errors.append({"row": row_num, "field": "value", "message": "Required."})
            is_valid = False
        else:
            try:
                value = int(value)
                if value < 2 or value > 5:
                    errors.append({"row": row_num, "field": "value", "message": "Grade value must be between 2 and 5."})
                    is_valid = False
            except ValueError:
                errors.append({"row": row_num, "field": "value", "message": "Grade value must be an integer."})
                is_valid = False

        # Validate grade_type
        valid_types = [c[0] for c in Grade.GradeTypeChoices.choices]
        if grade_type not in valid_types:
            errors.append({"row": row_num, "field": "grade_type", "message": f"Invalid type. Must be in {valid_types}."})
            is_valid = False

        # Validate graded_at
        graded_at = None
        if not graded_at_raw or pd.isna(graded_at_raw):
            errors.append({"row": row_num, "field": "graded_at", "message": "Required (format YYYY-MM-DD)."})
            is_valid = False
        else:
            try:
                graded_at = pd.to_datetime(graded_at_raw).date()
            except Exception:
                errors.append({"row": row_num, "field": "graded_at", "message": "Invalid date format."})
                is_valid = False
        
        action = "create"
        grade = None
        if is_valid:
            try:
                grade = Grade.objects.get(
                    student=student,
                    subject=subject,
                    grade_type=grade_type,
                    graded_at=graded_at
                )
                action = "update"
            except Grade.DoesNotExist:
                action = "create"
            except Grade.MultipleObjectsReturned:
                action = "update"
                grade = Grade.objects.filter(
                    student=student, subject=subject, grade_type=grade_type, graded_at=graded_at
                ).first()
                warnings.append({"row": row_num, "message": "Multiple identical grades found, updating the first one."})

            if self.mode == "create_only" and action == "update":
                warnings.append({"row": row_num, "message": "Grade already exists. Skipping."})
                action = "skip"
                is_valid = False
            elif self.mode == "update_only" and action == "create":
                warnings.append({"row": row_num, "message": "Grade not found. Skipping."})
                action = "skip"
                is_valid = False
                
        mapped_data = {}
        if is_valid and action != "skip":
            mapped_data = {
                "student": student,
                "subject": subject,
                "value": value,
                "grade_type": grade_type,
                "graded_at": graded_at,
                "comment": comment
            }
            if grade:
                mapped_data["instance"] = grade
                
        return (is_valid, action, mapped_data, errors, warnings)

    def commit_rows(self, rows_data: List[Dict[str, Any]]):
        for data in rows_data:
            instance = data.get("instance")
            
            if instance:
                instance.value = data["value"]
                instance.comment = data["comment"]
                instance.save()
            else:
                Grade.objects.create(
                    student=data["student"],
                    subject=data["subject"],
                    value=data["value"],
                    grade_type=data["grade_type"],
                    graded_at=data["graded_at"],
                    comment=data["comment"],
                )
