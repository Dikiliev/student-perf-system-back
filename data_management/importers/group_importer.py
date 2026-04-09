from typing import Dict, Any, Tuple, List
from students.models import Group
from users.models import User
from .base import ImporterService

class GroupImporter(ImporterService):
    EXPECTED_COLUMNS = ["name", "course", "curator_username"]

    def validate_row(self, row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any], List[Dict], List[Dict]]:
        errors = []
        warnings = []
        is_valid = True
        
        name = row.get("name")
        course = row.get("course")
        curator_username = row.get("curator_username")

        if not name:
            errors.append({"row": row_num, "field": "name", "message": "Group name is required."})
            is_valid = False
            
        if course is not None:
            try:
                course = int(course)
                if course < 1 or course > 6:
                    errors.append({"row": row_num, "field": "course", "message": "Course must be between 1 and 6."})
                    is_valid = False
            except ValueError:
                errors.append({"row": row_num, "field": "course", "message": "Course must be an integer."})
                is_valid = False
            
        curator = None
        if curator_username:
            try:
                curator = User.objects.get(username=curator_username)
            except User.DoesNotExist:
                errors.append({"row": row_num, "field": "curator_username", "message": f"User '{curator_username}' does not exist."})
                is_valid = False
                
        # Check action: create or update
        action = "create"
        group = None
        if is_valid:
            try:
                group = Group.objects.get(name=name)
                action = "update"
            except Group.DoesNotExist:
                action = "create"

            # Enforce modes
            if self.mode == "create_only" and action == "update":
                warnings.append({"row": row_num, "message": f"Group '{name}' already exists. Skipping due to create_only mode."})
                action = "skip"
                is_valid = False # Treat as skipped
            elif self.mode == "update_only" and action == "create":
                warnings.append({"row": row_num, "message": f"Group '{name}' not found. Skipping due to update_only mode."})
                action = "skip"
                is_valid = False
                
        mapped_data = {}
        if is_valid and action != "skip":
            mapped_data = {
                "name": name,
                "course": course if course else 1,
                "curator": curator
            }
            if group:
                mapped_data["instance"] = group
                
        return (is_valid, action, mapped_data, errors, warnings)

    def commit_rows(self, rows_data: List[Dict[str, Any]]):
        for data in rows_data:
            instance = data.get("instance")
            if instance:
                instance.course = data["course"]
                if data.get("curator"):
                    instance.curator = data["curator"]
                instance.save()
            else:
                Group.objects.create(
                    name=data["name"],
                    course=data["course"],
                    curator=data.get("curator")
                )
