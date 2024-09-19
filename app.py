import os
from pathlib import Path
import shutil
import tempfile
import customtkinter as ctk
from dotenv import load_dotenv
import pandas as pd
from tkinter import filedialog as fd

from helper.processing import bw_unit_normalize
from helper.getfile import GetFile
from view.main import MainView


class App(ctk.CTk):
    def __init__(self, start_size: tuple[int], env: dict = None):
        super().__init__()
        self.fileList: list[str] = [
            "Branch",
            "Building",
            "Enterprise",
            "Extranet",
            "IDC",
            "PCLD",
            "F5",
        ]
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.title("DBS | Grafana Reporting Automation")
        self.geometry(
            f"{start_size[0]}x{start_size[1]}+{(self.winfo_screenwidth() - start_size[0]) // 4}+{(self.winfo_screenheight() - start_size[1]) // 4}"
        )
        self.resizable(False, False)
        self.env = env if not None else None
        self.db: dict[str, pd.DataFrame] = self.__temp_file()
        MainView(master=self, controller=self).pack(fill="both", expand=True)

    def __temp_file(self) -> dict[str, pd.DataFrame]:
        tmpDir = os.path.join(tempfile.gettempdir(), "86c9817f304beed29e7faf6019dd3864")
        res = {}
        try:
            for id, file in enumerate(self.fileList):
                res[file] = pd.read_excel(
                    io=os.path.join(tmpDir, "db"), sheet_name=file
                ).apply(bw_unit_normalize, axis=1)
            return res
        except Exception:
            dbFile = fd.askopenfilename(
                title="DB File Not Found, Please Choose Database!",
                initialdir="~",
                filetypes=(
                    ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
                    ("All Files", "*.*"),
                ),
            )
            if dbFile != "":
                os.makedirs(name=tmpDir, exist_ok=True)
                shutil.copy2(src=Path(dbFile), dst=Path(os.path.join(tmpDir, "db")))
                self.__temp_file()
            else:
                self.destroy()


def environment() -> dict | None:
    if Path("./.env").is_file():
        load_dotenv(dotenv_path="./.env")
        return {}
    return None


app = App(start_size=(600, 700), env=environment())
app.mainloop()
