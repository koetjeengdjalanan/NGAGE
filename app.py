import os
from pathlib import Path
import shutil
import traceback
import customtkinter as ctk
import toml
import pandas as pd
from tkinter import filedialog as fd

from helper.processing import bw_unit_normalize
from helper.getfile import GetFile
from helper.readconfig import AppConfig
from view.ops_metric import OpsMetric
from view.tower_report import TowerReport


class App(ctk.CTk):
    def __init__(self, start_size: tuple[int], env: dict = {"DEV": False}):
        super().__init__()
        self.fileList: list[str] = [
            "Branch",
            "Building",
            "Enterprise",
            "Extranet",
            "IDC",
            "PCLD",
            "F5",
            "Firewall",
        ]
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.title("DBS | Grafana Reporting Automation")
        self.geometry(
            f"{start_size[0]}x{start_size[1]}+{(self.winfo_screenwidth() - start_size[0]) // 4}+{(self.winfo_screenheight() - start_size[1]) // 4}"
        )
        self.resizable(False, False)
        self.env = env
        self.config = AppConfig()
        self.lookUpTable: dict[str, pd.DataFrame] = self.__temp_file()
        tabView = ctk.CTkTabview(master=self)
        tabView.pack(fill="both", expand=True)
        tabView.add(name="Tower Report")
        TowerReport(master=tabView.tab(name="Tower Report"), controller=self).pack(
            fill="both", expand=True
        )
        tabView.add(name="Ops Metric")
        OpsMetric(master=tabView.tab(name="Ops Metric"), controller=self).pack(
            fill="both", expand=True
        )

    def __temp_file(self) -> dict[str, pd.DataFrame]:
        res = {}
        try:
            for id, file in enumerate(self.fileList):
                res[file] = pd.read_excel(
                    io=os.path.join(self.config.tmpDir, "LookupTable"), sheet_name=file
                )
                res[file] = (
                    res[file].apply(bw_unit_normalize, axis=1)
                    if file != self.fileList[-1]
                    else res[file]
                )
            return res
        # FIXME: Handle this exception properly by match the error message and appropriate action
        except Exception as err:
            print(err, traceback.format_exc(), sep="\n")
            print(Path(self.config.tmpDir).is_dir())
            lTFile = fd.askopenfilename(
                title=(
                    "Lookup Table File Not Found, Please Choose Lookup Table!"
                    if not Path(
                        os.path.join(self.config.tmpDir, "LookupTable")
                    ).is_file()
                    else f"{str(err)} | Choose Another Lookup Table!"
                ),
                initialdir="~",
                filetypes=(
                    ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
                    ("All Files", "*.*"),
                ),
            )
            # BUG: If user cancel the file dialog, the app will not close properly and if the file has been chose, the return value will be empty string
            if lTFile == "":
                self.destroy()
                return
            os.makedirs(name=self.config.tmpDir, exist_ok=True)
            shutil.copy2(
                src=Path(lTFile),
                dst=Path(os.path.join(self.config.tmpDir, "LookupTable")),
            )
            self.__temp_file()


# IDEA: Add a function to writ a default env file if not exist to tempdir and use it as default value and make it editable!
def environment() -> dict:
    envPath = Path("./.env.toml").absolute()
    if envPath.is_file():
        with open(envPath, "r") as file:
            return toml.load(file)
    return {
        "DEV": False,
    }


def handle_error(exception, value, tb):
    print(exception, value, tb)
    error_window = ctk.CTkToplevel(takefocus=True)
    error_window.title("An error has occurred")
    error_window.attributes("-topmost", True)
    error_window.bell()

    # Disable the main app window
    app.attributes("-disabled", True)

    def on_close():
        app.attributes("-disabled", False)
        error_window.destroy()
        app.destroy()

    def on_focus(event):
        error_window.bell()
        error_window.focus()

    error_window.bind("<FocusOut>", on_focus)

    ctk.CTkLabel(
        master=error_window, text=value, font=ctk.CTkFont(size=24, weight="bold")
    ).pack(pady=(20, 0), padx=20)
    error_message = ctk.CTkTextbox(master=error_window, wrap="none")
    error_message.insert(
        index="0.0", text=traceback.format_exc(chain=True), tags="error"
    )
    error_message.configure(state="disabled")
    error_message.pack(pady=20, padx=20, fill="both", expand=True)
    error_button = ctk.CTkButton(
        master=error_window,
        text="Close",
        command=on_close,
    )
    error_button.pack(pady=10, padx=20, side="right")


if __name__ == "__main__":
    import sys

    sys.excepthook = handle_error
    app = App(start_size=(600, 700), env=environment())
    app.report_callback_exception = handle_error
    app.mainloop()
