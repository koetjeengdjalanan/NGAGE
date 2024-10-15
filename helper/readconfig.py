from configparser import ConfigParser
from os import path
from tempfile import gettempdir
from pathlib import Path


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
