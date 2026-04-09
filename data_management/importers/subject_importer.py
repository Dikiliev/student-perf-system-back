from typing import Dict, Any, Tuple, List
from students.models import Subject
from .base import ImporterService

class SubjectImporter(ImporterService):
    EXPECTED_COLUMNS = ["name", "description"]

    def validate_row(self, row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any], List[Dict], List[Dict]]:
        errors = []
        warnings = []
        is_valid = True
        
        name = row.get("name")
        description = row.get("description") or ""

        if not name:
            errors.append({"row": row_num, "field": "name", "message": "Subject name is required."})
            is_valid = False
        
        action = "create"
        subject = None
        if is_valid:
            try:
                subject = Subject.objects.get(name=name)
                action = "update"
            except Subject.DoesNotExist:
                action = "create"

            if self.mode == "create_only" and action == "update":
                warnings.append({"row": row_num, "message": f"Subject '{name}' already exists. Skipping."})
                action = "skip"
                is_valid = False
            elif self.mode == "update_only" and action == "create":
                warnings.append({"row": row_num, "message": f"Subject '{name}' not found. Skipping."})
                action = "skip"
                is_valid = False
                
        mapped_data = {}
        if is_valid and action != "skip":
            mapped_data = {
                "name": name,
                "description": description
            }
            if subject:
                mapped_data["instance"] = subject
                
        return (is_valid, action, mapped_data, errors, warnings)

    def commit_rows(self, rows_data: List[Dict[str, Any]]):
        for data in rows_data:
            instance = data.get("instance")
            if instance:
                instance.description = data["description"]
                instance.save()
            else:
                Subject.objects.create(
                    name=data["name"],
                    description=data["description"]
                )
