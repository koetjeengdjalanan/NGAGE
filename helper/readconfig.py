from configparser import ConfigParser
from os import path, makedirs
import shutil
from tempfile import gettempdir
from pathlib import Path
from tkinter import filedialog as fd
import pandas as pd

from helper.processing import bw_unit_normalize


class AppConfig(ConfigParser):
    def __init__(self) -> None:
        super().__init__()
        self.tmpDir = Path(path.join(gettempdir(), "86c9817f304beed29e7faf6019dd3864"))
        if (
            not self.tmpDir.is_dir()
            or not Path(path.join(self.tmpDir, "config.ini")).is_file()
        ):
            self.tmpDir.mkdir(exist_ok=True, parents=True)
            self.set_default_config()
        self.read_file(open(Path(path.join(self.tmpDir, "config.ini"))))

    def set_default_config(self) -> None:
        self["cond_fmt"] = {
            "fmt0": {
                "type": "cell",
                "criteria": "=",
                "value": 0,
                "format": {
                    "num_format": "0.000 %%",
                    "bg_color": "#006400",
                    "font_color": "#FFFFFF",
                },
            },
            "fmt1": {
                "type": "cell",
                "criteria": "between",
                "minimum": 0,
                "maximum": 5 / 10,
                "format": {
                    "num_format": "0.000 %%",
                    "bg_color": "#299438",
                    "font_color": "#FFFFFF",
                },
            },
            "fmt2": {
                "type": "cell",
                "criteria": "between",
                "minimum": 5 / 10,
                "maximum": 7 / 10,
                "format": {
                    "num_format": "0.000 %%",
                    "bg_color": "#7ECC49",
                    "font_color": "#000000",
                },
            },
            "fmt3": {
                "type": "cell",
                "criteria": "between",
                "minimum": 7 / 10,
                "maximum": 8 / 10,
                "format": {
                    "num_format": "0.000 %%",
                    "bg_color": "#FF9933",
                    "font_color": "#000000",
                },
            },
            "fmt4": {
                "type": "cell",
                "criteria": ">=",
                "value": 8 / 10,
                "format": {
                    "num_format": "0.000 %%",
                    "bg_color": "#DB4035",
                    "font_color": "#FFFFFF",
                },
            },
        }
        with open(Path(path.join(self.tmpDir, "config.ini")), "w") as configfile:
            self.write(configfile)


def CopyLTFile(fileName: str) -> Path | None:
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
    lookUpTable: dict[str, pd.DataFrame] = pd.read_excel(io=filePath, sheet_name=None)
    for each in lookUpTable:
        if all(x in lookUpTable[each].columns for x in ["Unit", "Bandwidth"]):
            lookUpTable[each] = lookUpTable[each].apply(bw_unit_normalize, axis=1)
    return lookUpTable
