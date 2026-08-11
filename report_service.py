"""
Report generation service.
"""

import io
import pandas as pd


class ReportService:

    @staticmethod
    def generate_excel_report(df: pd.DataFrame) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Bao_Cao_OGSM", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Bao_Cao_OGSM"]

            header_format = workbook.add_format({
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#003366",
                "font_color": "#FFFFFF",
                "border": 1
            })

            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_format)
                worksheet.set_column(col_num, col_num, 18)

        output.seek(0)
        return output.read()
