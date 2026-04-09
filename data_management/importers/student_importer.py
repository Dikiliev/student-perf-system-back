from typing import Dict, Any, Tuple, List
from students.models import Student, Group
from .base import ImporterService

class StudentImporter(ImporterService):
    EXPECTED_COLUMNS = [
        "record_book_number", "last_name", "first_name", 
        "middle_name", "email", "group_name", 
        "enrollment_year", "status"
    ]

    def validate_row(self, row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any], List[Dict], List[Dict]]:
        errors = []
        warnings = []
        is_valid = True
        
        rbn = str(row.get("record_book_number") or "").strip()
        last_name = row.get("last_name")
        first_name = row.get("first_name")
        group_name = row.get("group_name")
        status = row.get("status") or "active"

        if not rbn:
            errors.append({"row": row_num, "field": "record_book_number", "message": "Required."})
            is_valid = False
            
        if not last_name or not first_name:
            errors.append({"row": row_num, "field": "name", "message": "First and last name are required."})
            is_valid = False

        group = None
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                errors.append({"row": row_num, "field": "group_name", "message": f"Group '{group_name}' not found."})
                is_valid = False
                
        # Validate status enum based on standard student statuses
        valid_statuses = [c[0] for c in Student.StatusChoices.choices]
        if status not in valid_statuses:
            errors.append({"row": row_num, "field": "status", "message": f"Invalid status '{status}'. Must be one of {valid_statuses}."})
            is_valid = False
        
        action = "create"
        student = None
        if is_valid:
            try:
                student = Student.objects.get(record_book_number=rbn)
                action = "update"
            except Student.DoesNotExist:
                action = "create"

            if self.mode == "create_only" and action == "update":
                warnings.append({"row": row_num, "message": f"Student '{rbn}' already exists. Skipping."})
                action = "skip"
                is_valid = False
            elif self.mode == "update_only" and action == "create":
                warnings.append({"row": row_num, "message": f"Student '{rbn}' not found. Skipping."})
                action = "skip"
                is_valid = False
                
        mapped_data = {}
        if is_valid and action != "skip":
            mapped_data = {
                "record_book_number": rbn,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": row.get("middle_name") or "",
                "email": row.get("email") or "",
                "group": group,
                "enrollment_year": row.get("enrollment_year"),
                "status": status,
            }
            if student:
                mapped_data["instance"] = student
                
        return (is_valid, action, mapped_data, errors, warnings)

    def commit_rows(self, rows_data: List[Dict[str, Any]]):
        for data in rows_data:
            instance = data.get("instance")
            
            # Extract common fields
            fields = {
                "last_name": data["last_name"],
                "first_name": data["first_name"],
                "middle_name": data["middle_name"],
                "email": data["email"],
                "group": data["group"],
                "status": data["status"],
            }
            
            if data["enrollment_year"]:
                fields["enrollment_year"] = data["enrollment_year"]
                
            if instance:
                for k, v in fields.items():
                    setattr(instance, k, v)
                instance.save()
            else:
                Student.objects.create(
                    record_book_number=data["record_book_number"],
                    **fields
                )
