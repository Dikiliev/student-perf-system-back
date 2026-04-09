import io
import pandas as pd
from typing import List, Dict

class ExporterService:
    @staticmethod
    def export_to_csv(data: List[Dict], headers: List[str] = None) -> bytes:
        df = pd.DataFrame(data)
        if headers and not df.empty:
            df = df[headers] # reorder and filter columns
        elif headers and df.empty:
            df = pd.DataFrame(columns=headers)
        
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue().encode('utf-8')

    @staticmethod
    def export_to_xlsx(data: List[Dict], headers: List[str] = None, sheet_name: str = "Data") -> bytes:
        df = pd.DataFrame(data)
        if headers and not df.empty:
            df = df[headers]
        elif headers and df.empty:
            df = pd.DataFrame(columns=headers)
            
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        return output.getvalue()
