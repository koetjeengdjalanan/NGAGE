"""Application configuration management and lookup-table utilities.

Provide ``AppConfig``, a ``ConfigParser`` subclass that persists its
state to a temporary directory, automatically applying version-based
resets. Also provide standalone helpers for copying lookup-table files
into the temp directory, reading multi-sheet Excel lookup tables with
bandwidth normalisation, and deserialising config sections into Python
data structures.
"""

import shutil
from configparser import ConfigParser
from json import loads as jLoads
from os import makedirs, path
from pathlib import Path
from tempfile import gettempdir
from tkinter import filedialog as fd
from typing import Any

import pandas as pd

from helper.processing import bw_unit_normalize


class AppConfig(ConfigParser):
    """Application configuration backed by a ``config.ini`` in a temp directory.

    On construction, load (or create) a config file at
    ``<tempdir>/<hash>/config.ini``. If the stored ``config_version``
    does not match ``CONFIG_VERSION``, or if ``reset`` is ``True``, the
    file is overwritten with factory defaults.

    Attributes:
        configEnum (list[dict]): Default conditional-formatting rule
            seed. Currently a single ``{"criteria": "="}`` entry.
        CONFIG_VERSION (str): Expected config file version. A mismatch
            triggers a reset to defaults.
        SKIP_ROWS (int): Default number of CSV header rows to skip.
        tmpDir (Path): Absolute path to the temporary directory where
            the config file is stored.
        skip_rows (int): Parsed value of the ``skip_rows`` setting from
            the ``preamble`` section.
    """

    configEnum: list[dict] = [{"criteria": "="}]
    CONFIG_VERSION: str = "0.7.0"
    SKIP_ROWS: int = 0

    def __init__(self, reset: bool = False) -> None:
        super().__init__()
        self.tmpDir = Path(path.join(gettempdir(), "86c9817f304beed29e7faf6019dd3864"))
        if not self.tmpDir.is_dir() or not Path(path.join(self.tmpDir, "config.ini")).is_file() or reset:
            self.set_default_config()
        try:
            if (preamble := GetConfigAsList(config=self, section="preamble")) and preamble.get(
                "config_version"
            ) != self.CONFIG_VERSION:
                self.set_default_config()
        except Exception:
            self.set_default_config()
        with open(Path(path.join(self.tmpDir, "config.ini")), "r") as f:
            self.read_file(f)
        self.skip_rows = self.getint("preamble", "skip_rows", fallback=self.SKIP_ROWS)

    def set_default_config(self) -> None:
        """Write factory-default configuration sections to disk.

        Create the temp directory if it does not exist and populate the
        config with three sections:

        * **preamble** — ``config_version`` and ``skip_rows``.
        * **fmt** — JSON-encoded conditional-format rules for Capacity
          and Availability exports (colour-coded percentage thresholds).
        * **availability** — comma-separated BSSB hostname list.
        """
        self.tmpDir.mkdir(exist_ok=True, parents=True)
        self["preamble"] = {"config_version": self.CONFIG_VERSION, "skip_rows": "0"}
        self["fmt"] = {
            "Capacity": (
                "["
                '{"type": "cell","criteria": "=","value": 0,'
                '"format": {"num_format": "0.000 %%","bg_color": "#006400","font_color": "#FFFFFF"}},'
                '{"type": "cell","criteria": "between","minimum": 0,"maximum": 0.5,'
                '"format": {"num_format": "0.000 %%","bg_color": "#299438","font_color": "#FFFFFF"}},'
                '{"type": "cell","criteria": "between","minimum": 0.5,"maximum": 0.7,'
                '"format": {"num_format": "0.000 %%","bg_color": "#7ECC49","font_color": "#000000"}},'
                '{"type": "cell","criteria": "between","minimum": 0.7,"maximum": 0.8,'
                '"format": {"num_format": "0.000 %%","bg_color": "#FF9933","font_color": "#000000"}},'
                '{"type": "cell","criteria": ">=","value": 0.8,'
                '"format": {"num_format": "0.000 %%","bg_color": "#DB4035","font_color": "#FFFFFF"}}'
                "]"
            ),
            "Availability": (
                "["
                '{"type": "cell","criteria": "<","value": 3,'
                '"format": {"num_format": "#,##0","bg_color": "#299438","font_color": "#FFFFFF"}},'
                '{"type": "cell","criteria": "between","minimum": 3,"maximum": 5,'
                '"format": {"num_format": "#,##0","bg_color": "#FF9933","font_color": "#000000"}},'
                '{"type": "cell","criteria": ">","value": 5,'
                '"format": {"num_format": "#,##0","bg_color": "#DB4035","font_color": "#FFFFFF"}}'
                "]"
            ),
        }
        self["availability"] = {
            "bssb_list": (
                "idjktpdc01extwr05,idjktpdc01extwr06,idjktpdc01extwr08,"
                "idjktsdc03extwr05,idjktsdc03extwr06,idjktsdc03extwr08"
            )
        }
        with open(Path(path.join(self.tmpDir, "config.ini")), "w") as configfile:
            self.write(configfile)

    def write_config(self) -> None:
        """Persist the current in-memory configuration to ``config.ini``.

        Overwrite the file at ``self.tmpDir / config.ini`` with all
        sections and options currently held by this ``ConfigParser``
        instance.
        """
        with open(Path(path.join(self.tmpDir, "config.ini")), "w") as configfile:
            self.write(configfile)


def CopyLTFile(fileName: str) -> Path | None:
    """Copy a user-selected lookup-table file into the temp directory.

    Open a file dialog prompting the user to select an Excel lookup-table
    file. If a file is selected, copy it into the ``AppConfig`` temp
    directory under the given ``fileName``. The dialog title is derived
    by stripping the ``.lt`` suffix from ``fileName``.

    Args:
        fileName (str): Destination file name (including extension) for
            the copied lookup table, e.g. ``"Capacity.lt"``.

    Returns:
        Path | None: The ``Path`` to the copied file inside the temp
            directory, or ``None`` if the user cancelled the dialog.
    """
    dest: Path = Path(path.join(AppConfig().tmpDir, fileName))
    lTFile = fd.askopenfilename(
        title=f"Choose {fileName.removesuffix('.lt')} Lookup Table",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        initialdir=Path.cwd(),
    )
    if not lTFile or lTFile is None:
        return None
    makedirs(name=AppConfig().tmpDir, exist_ok=True)
    shutil.copy2(src=Path(lTFile), dst=dest)
    return dest


def ReadLookupTable(filePath: Path) -> dict[str, pd.DataFrame]:
    """Read a multi-sheet Excel lookup table and normalise bandwidth units.

    Load every worksheet from ``filePath`` into a dictionary of
    DataFrames keyed by sheet name. For any sheet that contains both
    ``Unit`` and ``Bandwidth`` columns, apply ``bw_unit_normalize``
    row-wise to convert all bandwidth values to Mbps.

    Args:
        filePath (Path): Absolute path to the Excel file containing
            one or more lookup-table sheets.

    Returns:
        dict[str, pd.DataFrame]: Mapping of sheet names to DataFrames,
            with bandwidth-bearing sheets already normalised to Mbps.
    """
    lookUpTable: dict[str, pd.DataFrame] = pd.read_excel(io=filePath, sheet_name=None)
    for each in lookUpTable:
        if all(x in lookUpTable[each].columns for x in ["Unit", "Bandwidth"]):
            lookUpTable[each] = lookUpTable[each].apply(bw_unit_normalize, axis=1)
    return lookUpTable


def GetConfigAsList(config: AppConfig, section: str) -> dict[str, str | Any]:
    """Deserialise a config section into a dictionary of native Python objects.

    For each key in ``section``, check whether its value starts with
    ``"["`` (indicating a JSON array). If so, parse it with
    ``json.loads``; otherwise keep the raw string. This allows config
    values to hold either plain strings or JSON-encoded lists of
    dictionaries (e.g. conditional-format rules).

    Args:
        config (AppConfig): The application configuration instance to
            read from.
        section (str): The ``[section]`` name to retrieve.

    Returns:
        dict[str, str | Any]: A dictionary mapping option names to
            either their raw string values or parsed JSON objects.

    Raises:
        KeyError: If ``section`` does not exist in the configuration.
    """
    if config.has_section(section):
        return {key: jLoads(value) if value.startswith("[") else value for key, value in config.items(section)}
    else:
        raise KeyError(f"Section '{section}' not found in the configuration.")
