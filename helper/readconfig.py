from configparser import ConfigParser
from os import path, makedirs
import shutil
from tempfile import gettempdir
from pathlib import Path
from tkinter import filedialog as fd
from json import loads as jLoads
import pandas as pd

from helper.processing import bw_unit_normalize


class AppConfig(ConfigParser):
    configEnum: list[dict] = [{"criteria": "="}]

    def __init__(self, reset: bool = False) -> None:
        super().__init__()
        self.tmpDir = Path(path.join(gettempdir(), "86c9817f304beed29e7faf6019dd3864"))
        if (
            not self.tmpDir.is_dir()
            or not Path(path.join(self.tmpDir, "config.ini")).is_file()
            or reset
        ):
            self.tmpDir.mkdir(exist_ok=True, parents=True)
            self.set_default_config()
        self.read_file(open(Path(path.join(self.tmpDir, "config.ini"))))

    def set_default_config(self) -> None:
        self["fmt"] = {
            "Capacity": '[{"type": "cell","criteria": "=","value": 0,"format": {"num_format": "0.000 %%","bg_color": "#006400","font_color": "#FFFFFF"}},{"type": "cell","criteria": "between","minimum": 0,"maximum": 0.5,"format": {"num_format": "0.000 %%","bg_color": "#299438","font_color": "#FFFFFF"}},{"type": "cell","criteria": "between","minimum": 0.5,"maximum": 0.7,"format": {"num_format": "0.000 %%","bg_color": "#7ECC49","font_color": "#000000"}},{"type": "cell","criteria": "between","minimum": 0.7,"maximum": 0.8,"format": {"num_format": "0.000 %%","bg_color": "#FF9933","font_color": "#000000"}},{"type": "cell","criteria": ">=","value": 0.8,"format": {"num_format": "0.000 %%","bg_color": "#DB4035","font_color": "#FFFFFF"}}]',
            "Availability": '[{"type": "cell", "criteria": ">", "value": 3, "format": {"num_format": "0.000 %%", "bg_color": "#DB4035", "font_color": "#FFFFFF"}},{"type": "cell", "criteria": "<=", "value": 5, "format": {"num_format": "0.000 %%", "bg_color": "#DB4035", "font_color": "#FFFFFF"}}]',
        }
        self["availability"] = {
            "bssb_list": "idjktpdc01extwr05,idjktpdc01extwr06,idjktpdc01extwr08,idjktsdc03extwr05,idjktsdc03extwr06,idjktsdc03extwr08"
        }
        with open(Path(path.join(self.tmpDir, "config.ini")), "w") as configfile:
            self.write(configfile)

    def write_config(self) -> None:
        with open(Path(path.join(self.tmpDir, "config.ini")), "w") as configfile:
            self.write(configfile)


def CopyLTFile(fileName: str) -> Path | None:
    """
    Copy a lookup table file to a temporary directory.

    This function opens a file dialog for the user to select a lookup table file,
    then copies the selected file to a temporary directory.

    Args:
        fileName (str): The name of the file to be copied, including its extension.

    Returns:
        Path | None: The Path object representing the destination of the copied file in
        the temporary directory, or None if no file was selected.
    """
    dest: Path = Path(path.join(AppConfig().tmpDir, fileName))
    lTFile = fd.askopenfilename(
        title=f"Choose {fileName.removesuffix('.lt')} Lookup Table",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        initialdir="~",
    )
    if not lTFile or lTFile is None:
        return None
    makedirs(name=AppConfig().tmpDir, exist_ok=True)
    shutil.copy2(src=Path(lTFile), dst=dest)
    return dest


def ReadLookupTable(filePath: Path) -> dict[str, pd.DataFrame]:
    """
    Read an Excel file containing lookup tables and normalize bandwidth units.

    This function reads all sheets from an Excel file, storing each sheet as a DataFrame
    in a dictionary. For sheets containing 'Unit' and 'Bandwidth' columns, it applies
    bandwidth unit normalization.

    Args:
        filePath (Path): The file path of the Excel file to be read.

    Returns:
        dict[str, pd.DataFrame]: A dictionary where keys are sheet names and values
        are the corresponding DataFrames. Sheets with 'Unit' and 'Bandwidth' columns
        have their bandwidth units normalized.
    """
    lookUpTable: dict[str, pd.DataFrame] = pd.read_excel(io=filePath, sheet_name=None)
    for each in lookUpTable:
        if all(x in lookUpTable[each].columns for x in ["Unit", "Bandwidth"]):
            lookUpTable[each] = lookUpTable[each].apply(bw_unit_normalize, axis=1)
    return lookUpTable


def GetConfigAsList(config: AppConfig, section: str) -> dict[str, list[dict]]:
    """
    Get a specified section as a dictionary of lists.

    Args:
        config (AppConfig): The application configuration object.
        section (str): The section name.

    Returns:
        dict[str, list[dict]]: A dictionary where values are lists of dictionaries.
    """
    if config.has_section(section):
        return {
            key: jLoads(value) if value.startswith("[") else value
            for key, value in config.items(section)
        }
    else:
        raise KeyError(f"Section '{section}' not found in the configuration.")
