"""Extended file processor for conditional formatting and multi-file selection.

Extend ``FileHandler`` with the ability to export DataFrames to Excel
with xlsxwriter conditional-formatting rules and to open a multi-file
selection dialog that concatenates several CSV files into a single
DataFrame.
"""

from pathlib import Path
from tkinter import filedialog as fd
from typing import Dict, List

import pandas as pd

from helper.filehandler import FileHandler


class ExtendedFileProcessor(FileHandler):
    """File processor with conditional formatting and multi-file capabilities.

    Inherit from ``FileHandler`` and add ``ext_export`` for writing
    xlsxwriter conditional formats and ``select_files`` for opening a
    dialog that lets the user pick multiple CSV files at once.

    Attributes:
        sourceFiles (tuple[Path, ...]): Tuple of ``Path`` objects for
            all files selected via ``select_files``. Empty by default.
    """

    sourceFiles: tuple[Path, ...] = ()

    def ext_export(
        self, data: Dict[str, pd.DataFrame], rules: List[Dict], colList: List[str]
    ) -> "ExtendedFileProcessor":
        """Export multiple DataFrames to Excel with conditional formatting.

        Write each DataFrame in ``data`` to a separate worksheet in the
        Excel file at ``self.savedFile``. For columns whose headers
        contain any of the strings in ``colList``, apply every
        conditional-format rule defined in ``rules``.

        Args:
            data (Dict[str, pd.DataFrame]): Mapping of sheet names to
                DataFrames. Each key becomes a worksheet name.
            rules (List[Dict]): List of conditional-format rule
                dictionaries compatible with xlsxwriter's
                ``worksheet.conditional_format`` API. Each dict must
                include ``type``, ``criteria``, and ``format`` keys and
                may include ``minimum``, ``maximum``, or ``value``.
            colList (List[str]): Substrings used to identify which
                columns should receive conditional formatting. A column
                is formatted if its header contains any of these strings.

        Raises:
            ValueError: If ``data`` is not a dictionary.

        Returns:
            ExtendedFileProcessor: ``self``, to allow method chaining.
        """
        data = data if data is not None else self.sourceData
        if not isinstance(data, dict):
            raise ValueError("Invalid Data Type", type(data))
        writer = pd.ExcelWriter(path=self.savedFile, engine="xlsxwriter")
        workbook = writer.book

        def percent_cond_fmt(worksheet, df) -> None:
            """Apply conditional formatting rules to matching columns.

            Args:
                worksheet: The xlsxwriter ``Worksheet`` object.
                df (pd.DataFrame): The DataFrame written to this sheet,
                    used to determine column indices and row count.
            """
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
        """Open a multi-file dialog, read the selected CSVs, and concatenate them.

        Present a file dialog allowing the user to select one or more CSV
        files. Read each selected file (skipping ``skipRows`` header rows)
        and concatenate the resulting DataFrames into a single DataFrame
        stored in ``self.sourceData``. After processing, ``sourceFile``
        is set to ``None`` and ``sourceFiles`` holds the selected paths.

        Args:
            title (str, optional): Title text displayed on the file
                dialog window. Defaults to ``"Select Multiple Files"``.
            skipRows (int, optional): Number of leading rows to skip
                when reading each CSV file. Defaults to ``0``.

        Returns:
            ExtendedFileProcessor: ``self``, to allow method chaining.
                If no files are selected the instance is returned
                unchanged.
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
            if self.sourceData is not None:
                resData = pd.concat([resData, self.sourceData], ignore_index=True)
        self.sourceData = resData
        self.sourceFile = None
        return self
