from pathlib import Path
from typing import Dict
import pandas as pd


class ExtendedExcelProcessor:
    def __init__(self, resFileLoc: Path, data: Dict[str, pd.DataFrame]) -> None:
        self.resFileLoc = resFileLoc
        self.data = data

    def export_excel(self) -> "ExtendedExcelProcessor":
        """Export DataFrame to Excel

        Raises:
            ValueError: Invalid Data Type

        Returns:
            ExtendedExcelProcessor: ExtendedExcelProcessor Class Object
        """
        if not isinstance(self.data, dict):
            raise ValueError("Invalid Data Type", type(self.data))
        writer = pd.ExcelWriter(path=self.resFileLoc, engine="xlsxwriter")
        workbook = writer.book

        def percent_cond_fmt(worksheet, df) -> None:
            redBg = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#ff0000"}
            )
            orgBg = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#ffc000"}
            )
            greBg = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#00b050"}
            )
            colLs = df.columns.str.contains("%").nonzero()[0].tolist()
            for colId in colLs:
                worksheet.conditional_format(
                    1,
                    colId,
                    len(df),
                    colId,
                    {
                        "type": "cell",
                        "criteria": "<=",
                        "value": 6 / 10,
                        "format": greBg,
                    },
                )
                worksheet.conditional_format(
                    1,
                    colId,
                    len(df),
                    colId,
                    {
                        "type": "cell",
                        "criteria": ">",
                        "value": 7 / 10,
                        "format": redBg,
                    },
                )
                worksheet.conditional_format(
                    1,
                    colId,
                    len(df),
                    colId,
                    {
                        "type": "cell",
                        "criteria": "between",
                        "minimum": 6 / 10,
                        "maximum": 7 / 10,
                        "format": orgBg,
                    },
                )

        for key in self.data.keys():
            df = pd.DataFrame(data=self.data[key])
            df.to_excel(excel_writer=writer, sheet_name=key, index=False)
            worksheet = writer.sheets[key]
            worksheet.autofit()
            percent_cond_fmt(worksheet, df)
        writer.close()
        return self
