# data_management/services/predictions.py
from typing import List

def trigger_prediction_recalculation(student_ids: List[int]):
    """
    Triggers prediction recalculation for the given student IDs.
    This safely imports the specific prediction logic so there are no circular imports.
    """
    # Import locally because the analytics app might depend on students / logic
    from students.models import Student
    from analytics.services import calculate_prediction_for_student
    
    students = Student.objects.filter(id__in=student_ids)
    for student in students:
        calculate_prediction_for_student(student.id)
