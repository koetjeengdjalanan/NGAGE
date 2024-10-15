from typing import Dict
import pandas as pd

from helper.filehandler import FileHandler


class ExtendedExcelProcessor(FileHandler):
    def ext_export(self, data: Dict[str, pd.DataFrame]) -> "ExtendedExcelProcessor":
        """Export DataFrame to Excel

        Raises:
            ValueError: Invalid Data Type

        Returns:
            ExtendedExcelProcessor: ExtendedExcelProcessor Class Object
        """
        data = data if data is not None else self.sourceData
        if not isinstance(data, dict):
            raise ValueError("Invalid Data Type", type(data))
        writer = pd.ExcelWriter(path=self.savedFile, engine="xlsxwriter")
        workbook = writer.book

        def percent_cond_fmt(worksheet, df) -> None:
            purGr = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#006400"}
            )
            greBg = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#299438"}
            )
            lgtGr = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#7ECC49"}
            )
            orgBg = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#FF9933"}
            )
            redBg = workbook.add_format(
                {"num_format": "0.000 %", "bg_color": "#DB4035"}
            )
            colLs = df.columns.str.contains("%").nonzero()[0].tolist()
            colLs += df.columns.str.contains("cpu").nonzero()[0].tolist()
            for colId in colLs:
                worksheet.conditional_format(
                    1,
                    colId,
                    len(df),
                    colId,
                    {
                        "type": "cell",
                        "criteria": "=",
                        "value": 0,
                        "format": purGr,
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
                        "value": 8 / 10,
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
                        "minimum": 7 / 10,
                        "maximum": 8 / 10,
                        "format": orgBg,
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
                        "minimum": 5 / 10,
                        "maximum": 7 / 10,
                        "format": lgtGr,
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
                        "minimum": 0,
                        "maximum": 5 / 10,
                        "format": greBg,
                    },
                )

        for key in data.keys():
            df = pd.DataFrame(data=data[key])
            df.to_excel(
                excel_writer=writer, sheet_name=key, index=False, na_rep="=NA()"
            )
            worksheet = writer.sheets[key]
            percent_cond_fmt(worksheet, df)
            worksheet.autofit()
            worksheet.freeze_panes(1, 0)
        writer.close()
        return self
