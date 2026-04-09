import pandas as pd
import math
from typing import List, Dict, Any, Tuple
from django.db import transaction

class ImporterService:
    """
    Base service for parsing, validating, and committing CSV/XLSX data.
    """
    
    # Needs to be overridden by subclasses
    EXPECTED_COLUMNS: List[str] = []
    
    def __init__(self, file_obj, file_format: str, mode: str = "upsert"):
        self.file_obj = file_obj
        self.file_format = file_format
        self.mode = mode  # create_only, update_only, upsert
        
        self.total_rows = 0
        self.valid_rows = 0
        self.invalid_rows = 0
        
        self.created_candidates = 0
        self.updated_candidates = 0
        
        self.row_errors = []
        self.row_warnings = []
        self.valid_data_rows = []
        
    def _read_file(self) -> pd.DataFrame:
        try:
            if self.file_format == "csv":
                # Try to auto-detect separator, default to comma
                df = pd.read_csv(self.file_obj, sep=None, engine='python', encoding='utf-8')
            elif self.file_format == "xlsx":
                df = pd.read_excel(self.file_obj)
            else:
                raise ValueError(f"Unsupported format: {self.file_format}")
            
            # Clean dataframe (replace NaN with None, strip strings)
            df = df.where(pd.notnull(df), None)
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            return df
        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    def validate(self) -> Dict[str, Any]:
        """
        Parses the file and validates all rows without committing.
        Returns the validation summary.
        """
        df = self._read_file()
        
        # Check columns
        missing_columns = [col for col in self.EXPECTED_COLUMNS if col not in df.columns]
        if missing_columns:
            return {
                "error": f"Missing required columns: {', '.join(missing_columns)}",
                "total_rows": 0,
            }
            
        self.total_rows = len(df)
        
        for index, row in df.iterrows():
            row_num = index + 2  # +1 for 0-index, +1 for header
            row_dict = row.to_dict()
            
            # Subclasses will implement this to validate and map the row
            is_valid, action, mapped_data, errors, warnings = self.validate_row(row_dict, row_num)
            
            if warnings:
                self.row_warnings.extend(warnings)
                
            if is_valid:
                self.valid_rows += 1
                self.valid_data_rows.append(mapped_data)
                if action == "create":
                    self.created_candidates += 1
                elif action == "update":
                    self.updated_candidates += 1
            else:
                self.invalid_rows += 1
                self.row_errors.extend(errors)
                
        return self._build_summary()
        
    def commit(self) -> Dict[str, Any]:
        """
        Commits valid parsed rows to the database.
        Must be called AFTER validate().
        """
        if self.invalid_rows > 0:
            return {"error": "Cannot commit file with invalid rows. Fix errors and try again."}
            
        if self.total_rows == 0:
            # Need to run validate if not run
            self.validate()
            if self.row_errors:
                return self._build_summary()
                
        try:
            with transaction.atomic():
                self.commit_rows(self.valid_data_rows)
            return self._build_summary()
        except Exception as e:
            return {"error": f"Commit failed: {str(e)}"}

    def _build_summary(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "created_candidates": self.created_candidates,
            "update_candidates": self.updated_candidates,
            "row_errors": self.row_errors,
            "row_warnings": self.row_warnings,
        }

    # -- Methods to Override --
    
    def validate_row(self, row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any], List[Dict], List[Dict]]:
        """
        Must return (is_valid, action, mapped_data, errors, warnings)
        action is either 'create', 'update', or 'skip'
        """
        raise NotImplementedError("Subclasses must implement validate_row")
        
    def commit_rows(self, rows_data: List[Dict[str, Any]]):
        """
        Perform the bulk insert/update operation safely.
        """
        raise NotImplementedError("Subclasses must implement commit_rows")
