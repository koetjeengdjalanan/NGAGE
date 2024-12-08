from pathlib import Path
from typing import Dict, List
import pandas as pd
from tkinter import filedialog as fd

from helper.filehandler import FileHandler


class ExtendedFileProcessor(FileHandler):
    sourceFiles: tuple[Path] = ()

    def ext_export(
        self, data: Dict[str, pd.DataFrame], rules: List[Dict], colList: List[str]
    ) -> "ExtendedFileProcessor":
        """Export DataFrame to Excel

        Raises:
            ValueError: Invalid Data Type

        Returns:
            ExtendedFileProcessor: ExtendedFileProcessor Class Object
        """
        data = data if data is not None else self.sourceData
        if not isinstance(data, dict):
            raise ValueError("Invalid Data Type", type(data))
        writer = pd.ExcelWriter(path=self.savedFile, engine="xlsxwriter")
        workbook = writer.book

        def percent_cond_fmt(worksheet, df) -> None:
            colLs = df.columns.str.contains(colList[0]).nonzero()[0].tolist()
            for key in colList[1:]:
                colLs += df.columns.str.contains(key).nonzero()[0].tolist()
            for colId in colLs:
                for rule in rules:
                    if rule["criteria"] in ("between", ">=", "<=", "=", "<", ">"):
                        conditional_criteria = {
                            "type": rule["type"],
                            "criteria": rule["criteria"],
                            "format": workbook.add_format(rule["format"]),
                        }
                        if rule["criteria"] == "between":
                            conditional_criteria["minimum"] = rule["minimum"]
                            conditional_criteria["maximum"] = rule["maximum"]
                        elif "value" in rule:
                            conditional_criteria["value"] = rule["value"]
                    worksheet.conditional_format(
                        1, colId, len(df), colId, conditional_criteria
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

    def select_files(
        self, title: str = "Select Multiple Files", skipRows: int = 0
    ) -> "ExtendedFileProcessor":
        """
        Opens a file dialog for selecting multiple CSV files, reads them, and concatenates their data.

        This method allows the user to select multiple CSV files through a file dialog.
        It then reads each selected file, skipping the specified number of rows,
        and combines all the data into a single DataFrame.

        Args:
            title (str, optional): The title of the file dialog window. Defaults to "Select Multiple Files".
            skipRows (int, optional): The number of rows to skip when reading each file. Defaults to 0.

        Returns:
            ExtendedFileProcessor: The instance of the class, allowing for method chaining.

        Note:
            If no files are selected, the method returns the current instance without changes.
            After processing, sourceFile is set to None and sourceData contains the combined data from all selected files.
        """
        filetype = (("CSV Files", "*.csv"),)
        resData: pd.DataFrame = pd.DataFrame()
        res = fd.askopenfilenames(
            title=title, initialdir=self.initDir, filetypes=filetype
        )
        if not res:
            return self
        self.sourceFiles = tuple(Path(path).absolute() for path in res)
        for _ in self.sourceFiles:
            self.sourceFile = _
            self.read_file(skipRows=skipRows)
            resData = pd.concat([resData, self.sourceData], ignore_index=True)
        self.sourceData = resData
        self.sourceFile = None
        return self
