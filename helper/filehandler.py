"""Core file-handling utilities for dialogs, reading, writing, and encoding detection.

Provide the ``FileHandler`` class that encapsulates Tkinter file
dialogs, automatic character-encoding detection via ``chardet``, and
read/write operations for CSV and Excel files using ``pandas``.
"""

from datetime import datetime
from pathlib import Path
from tkinter import filedialog as fd
from typing import Any, Dict, List, Optional, Union

import chardet
import pandas as pd


class FileHandler:
    """Manage file selection dialogs, encoding detection, and data I/O.

    Wrap Tkinter file dialogs for selecting source files, choosing save
    locations, and picking directories. Detect file encoding with
    ``chardet``, read CSV and Excel files into pandas DataFrames, and
    export DataFrames back to Excel via xlsxwriter. Also provide a
    cross-platform file-explorer launcher.

    Attributes:
        sourceFile (Path | None): Path to the currently selected source
            file, or ``None`` if no file has been selected.
        sourceData (pd.DataFrame | None): DataFrame loaded from
            ``sourceFile``, or ``None`` before reading.
        initDir (Path): Initial directory shown in file dialogs.
            Defaults to the user's home directory.
        destDir (Path): Destination directory used as fallback for save
            dialogs. Defaults to the current working directory.
        savedFile (Path): Path where exported files are written.
            Defaults to ``./saved.xlsx``.
        encodingList (list[str]): Exhaustive list of Python codec names
            used to validate the encoding detected by ``chardet``.
    """

    def __init__(
        self,
        sourceFile: Optional[Path] = None,
        sourceData: Optional[pd.DataFrame] = None,
        initDir: Path = Path().home().absolute(),
        destDir: Path = Path().cwd(),
        savedFile: Path = Path("./saved.xlsx").absolute(),
    ) -> None:
        """Initialize the file handler with optional source and destination paths.

        Args:
            sourceFile (Path | None, optional): Pre-selected source file
                path. Defaults to ``None``.
            sourceData (pd.DataFrame | None, optional): Pre-loaded
                DataFrame to use as source data. Defaults to ``None``.
            initDir (Path, optional): Initial directory for file dialogs.
                Defaults to the user's home directory.
            destDir (Path, optional): Default destination directory for
                save dialogs. Defaults to the current working directory.
            savedFile (Path, optional): Default output file path.
                Defaults to ``./saved.xlsx``.
        """
        self.sourceFile = sourceFile
        self.sourceData = sourceData
        self.initDir = initDir
        self.destDir = destDir
        self.savedFile = savedFile
        self.encodingList: list = [
            "ascii",
            "big5",
            "big5hkscs",
            "cp037",
            "cp273",
            "cp424",
            "cp437",
            "cp500",
            "cp720",
            "cp737",
            "cp775",
            "cp850",
            "cp852",
            "cp855",
            "cp856",
            "cp857",
            "cp858",
            "cp860",
            "cp861",
            "cp862",
            "cp863",
            "cp864",
            "cp865",
            "cp866",
            "cp869",
            "cp874",
            "cp875",
            "cp932",
            "cp949",
            "cp950",
            "cp1006",
            "cp1026",
            "cp1125",
            "cp1140",
            "cp1250",
            "cp1251",
            "cp1252",
            "cp1253",
            "cp1254",
            "cp1255",
            "cp1256",
            "cp1257",
            "cp1258",
            "euc-jp",
            "euc-jis-2004",
            "euc-jisx0213",
            "euc-kr",
            "gb2312",
            "gbk",
            "gb18030",
            "hz",
            "iso2022-jp",
            "iso2022-jp-1",
            "iso2022-jp-2",
            "iso2022-jp-2004",
            "iso2022-jp-3",
            "iso2022-jp-ext",
            "iso2022-kr",
            "latin-1",
            "iso8859-2",
            "iso8859-3",
            "iso8859-4",
            "iso8859-5",
            "iso8859-6",
            "iso8859-7",
            "iso8859-8",
            "iso8859-9",
            "iso8859-10",
            "iso8859-11",
            "iso8859-13",
            "iso8859-14",
            "iso8859-15",
            "iso8859-16",
            "johab",
            "koi8-r",
            "koi8-t",
            "koi8-u",
            "kz1048",
            "mac-cyrillic",
            "mac-greek",
            "mac-iceland",
            "mac-latin2",
            "mac-roman",
            "mac-turkish",
            "ptcp154",
            "shift-jis",
            "shift-jis-2004",
            "shift-jisx0213",
            "utf-32",
            "utf-32-be",
            "utf-32-le",
            "utf-16",
            "utf-16-be",
            "utf-16-le",
            "utf-7",
            "utf-8",
            "utf-8-sig",
        ]

    def select_directory(self, dirStr: str | Path = Path().home().absolute()) -> "FileHandler":
        """Open a directory-selection dialog and store the chosen path.

        Present a Tkinter ``askdirectory`` dialog starting at ``dirStr``.
        If the user selects a directory, update ``self.initDir`` with the
        absolute path; otherwise retain the previous value.

        Args:
            dirStr (str | Path, optional): Starting directory for the
                dialog. Defaults to the user's home directory.

        Returns:
            FileHandler: ``self``, to allow method chaining.
        """
        destDirectory = fd.askdirectory(
            initialdir=dirStr,
            mustexist=True,
            title="Select Directory / Folder",
        )
        self.initDir = Path(destDirectory).absolute() if destDirectory != "" else self.initDir
        return self

    def save_file_loc(
        self,
        fileName="EXPORT.xlsx",
        dirStr: str | Path = Path().home().absolute(),
        timeStamp: bool = True,
        promptDialog: bool = True,
    ) -> "FileHandler":
        """Open a save-file dialog and store the chosen destination path.

        Optionally prepend a ``YYYYMMDD_HHMMSS`` timestamp to the file
        name. When ``promptDialog`` is ``False``, skip the dialog and
        build the path from ``dirStr`` and ``fileName`` directly.

        Args:
            fileName (str, optional): Base file name for the export.
                Defaults to ``"EXPORT.xlsx"``.
            dirStr (str | Path, optional): Starting directory for the
                dialog, or the target directory when ``promptDialog`` is
                ``False``. Defaults to the user's home directory.
            timeStamp (bool, optional): Prepend a timestamp to
                ``fileName`` when ``True``. Defaults to ``True``.
            promptDialog (bool, optional): Show the save-file dialog
                when ``True``; construct the path silently when
                ``False``. Defaults to ``True``.

        Returns:
            FileHandler: ``self``, to allow method chaining.
        """
        if timeStamp:
            fileName = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-{fileName}"
        filetype = (
            ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*"),
        )
        res = (
            fd.asksaveasfilename(
                title="Save File As ...",
                initialdir=dirStr if dirStr != "" else self.destDir,
                filetypes=filetype,
                defaultextension=".xlsx",
                initialfile=fileName,
                confirmoverwrite=True,
            )
            if promptDialog
            else f"{dirStr}/{fileName}"
        )
        self.savedFile = Path(res).absolute() if res != "" else self.savedFile
        return self

    def select_file(self, title: str = "Open Source File") -> "FileHandler":
        """Open a file-selection dialog for CSV or Excel files.

        Present a Tkinter ``askopenfilename`` dialog filtered to CSV,
        Excel, and all-file types. If the user selects a file, store its
        absolute path in ``self.sourceFile``; otherwise retain the
        previous value.

        Args:
            title (str, optional): Title text for the dialog window.
                Defaults to ``"Open Source File"``.

        Returns:
            FileHandler: ``self``, to allow method chaining.
        """
        filetype = (
            ("CSV Files", "*.csv"),
            ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
            ("All Files", "*.*"),
        )
        res = fd.askopenfilename(title=title, initialdir=self.initDir, filetypes=filetype)
        self.sourceFile = Path(res).absolute() if res != "" else self.sourceFile
        return self

    def encoder_detect(self) -> dict[str, Any] | None:
        """Detect the character encoding of the current source file.

        Read the raw bytes of ``self.sourceFile`` and pass them to
        ``chardet.detect``. If the detected encoding is recognised
        (i.e. present in ``self.encodingList``), return the full
        detection result; otherwise return ``None``.

        Returns:
            dict[str, Any] | None: A ``chardet`` result dictionary with
                keys ``encoding``, ``confidence``, and ``language``, or
                ``None`` when the source file is unset or the detected
                encoding is not in the supported list.
        """
        source_file = self.sourceFile
        if source_file is None:
            return None
        with open(source_file, "rb") as file:
            data = file.read()
            res = chardet.detect(data)
            encoding = res.get("encoding")
            if encoding is not None and encoding.lower() in self.encodingList:
                return dict(res)
            else:
                return None

    def read_file(self, skipRows: int = 0) -> "FileHandler":
        """Read the source file into a pandas DataFrame.

        Dispatch to ``pd.read_csv`` for ``.csv`` files and
        ``pd.read_excel`` for Excel files (``.xlsx``, ``.xls``,
        ``.xlsm``, ``.xlsb``). For CSV files, encoding is validated
        via ``encoder_detect`` before reading. The resulting DataFrame
        is stored in ``self.sourceData``.

        Args:
            skipRows (int, optional): Number of leading rows to skip
                when reading the file. Defaults to ``0``.

        Raises:
            FileNotFoundError: If ``self.sourceFile`` is ``None`` or
                does not point to an existing file.
            ValueError: If the detected encoding for a CSV file is not
                in the supported encoding list.
            TypeError: If the file extension is not a recognised CSV or
                Excel format.

        Returns:
            FileHandler: ``self``, to allow method chaining.
        """
        source_file = self.sourceFile
        if source_file is None or not source_file.is_file():
            raise FileNotFoundError(f"{source_file} is not a file!")
        match source_file.suffix:
            case ".csv":
                if self.encoder_detect() is None:
                    raise ValueError("Invalid Encoding", self.encoder_detect())
                self.sourceData = pd.read_csv(
                    filepath_or_buffer=source_file, skiprows=skipRows, on_bad_lines="skip", skip_blank_lines=True
                )
            case ".xlsx" | ".xls" | ".xlsm" | ".xlsb":
                self.sourceData = pd.read_excel(io=source_file, skiprows=skipRows)
            case _:
                raise TypeError("Invalid File Type", source_file.suffix)
        return self

    def export_excel(
        self,
        data: Optional[Union[pd.DataFrame, Dict[str, Union[List, pd.DataFrame, Dict[str, Any]]]]] = None,
    ) -> "FileHandler":
        """Export data to an Excel file via xlsxwriter.

        Accept either a single ``DataFrame`` (written to "Sheet1") or a
        dictionary mapping sheet names to DataFrames (each written to
        its own worksheet). If ``data`` is ``None``, fall back to
        ``self.sourceData``.

        Args:
            data (pd.DataFrame | dict | None, optional): Data to export.
                A ``DataFrame`` is written as a single sheet; a ``dict``
                of DataFrames produces one sheet per key. Defaults to
                ``None``, in which case ``self.sourceData`` is used.

        Raises:
            ValueError: If ``data`` is neither a ``DataFrame`` nor a
                ``dict``.

        Returns:
            FileHandler: ``self``, to allow method chaining.
        """
        data = data if data is not None else self.sourceData
        writer = pd.ExcelWriter(path=self.savedFile, engine="xlsxwriter")
        match data:
            case pd.DataFrame():
                data.to_excel(excel_writer=writer, sheet_name="Sheet1")
                writer.close()
            case dict():
                for key in data.keys():
                    pd.DataFrame(data=data[key]).to_excel(excel_writer=writer, sheet_name=key)
                writer.close()
            case _:
                raise ValueError("Invalid Data Type", type(data))
        return self

    def flatten_dict(self, data: dict, parent_key: str = "", sep: str = "_", level: int = 1) -> dict:
        """Flatten a nested dictionary up to a specified depth.

        Recursively merge nested dictionary keys using ``sep`` as a
        delimiter. Stop recursing when ``level`` reaches zero, leaving
        deeper nested structures as-is.

        Args:
            data (dict): The dictionary to flatten.
            parent_key (str, optional): Prefix prepended to each key
                during recursion. Defaults to ``""``.
            sep (str, optional): Separator inserted between parent and
                child keys. Defaults to ``"_"``.
            level (int, optional): Maximum nesting levels to flatten.
                Defaults to ``1``.

        Returns:
            dict: A new dictionary with nested keys joined by ``sep``.
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key != "" else key
            if isinstance(value, dict) and level > 0:
                items.extend(self.flatten_dict(data=value, parent_key=new_key, level=level - 1).items())
            else:
                items.append((new_key, value))
        return dict(items)

    def open_explorer(self) -> "FileHandler":
        """Open the native file explorer highlighting the saved file.

        Detect the current operating system and launch the appropriate
        file manager: ``explorer`` on Windows, ``open -R`` on macOS,
        or ``xdg-open`` on Linux. The explorer opens to the directory
        containing ``self.savedFile``.

        Returns:
            FileHandler: ``self``, to allow method chaining.
        """
        from platform import system
        from subprocess import run

        match system():
            case "Windows":
                run(args=["explorer", "/select,", self.savedFile])
            case "Darwin":
                run(args=["open", "-R", self.savedFile])
            case "Linux":
                run(args=["xdg-open", self.savedFile.parent])

        return self
