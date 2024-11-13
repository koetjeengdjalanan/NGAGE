from configparser import ConfigParser
from os import path
from tempfile import gettempdir
from pathlib import Path
from tkinter import filedialog as fd
import traceback

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


def LookUpTable(fileList: list[str]) -> dict[str, pd.DataFrame]:
    res = {}
    try:
        for id, file in enumerate(fileList):
            res[file] = pd.read_excel(
                io=path.join(AppConfig().tmpDir, "LookupTable"), sheet_name=file
            )
            res[file] = (
                res[file].apply(bw_unit_normalize, axis=1)
                if file != fileList[-1]
                else res[file]
            )
        return res
    except Exception as err:
        print(err, traceback.format_exc(), sep="\n")
        print(Path(AppConfig().tmpDir).is_dir())
        lTFile = fd.askopenfilename(
            title=(
                "Lookup Table File Not Found, Please Choose Lookup Table!"
                if not Path(path.join(AppConfig().tmpDir, "LookupTable")).is_file()
                else f"{str(err)} | Choose Another Lookup Table!"
            ),
        )
