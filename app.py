import os
from pathlib import Path
import shutil
import tempfile
import traceback
import customtkinter as ctk
import toml
import pandas as pd
from tkinter import filedialog as fd

from helper.processing import bw_unit_normalize
from helper.getfile import GetFile
from view.main import MainView


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
        ]
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.title("DBS | Grafana Reporting Automation")
        self.geometry(
            f"{start_size[0]}x{start_size[1]}+{(self.winfo_screenwidth() - start_size[0]) // 4}+{(self.winfo_screenheight() - start_size[1]) // 4}"
        )
        self.resizable(False, False)
        self.env = env
        self.tmpDir = os.path.join(
            tempfile.gettempdir(), "86c9817f304beed29e7faf6019dd3864"
        )
        self.lookUpTable: dict[str, pd.DataFrame] = self.__temp_file()
        MainView(master=self, controller=self).pack(fill="both", expand=True)

    def __temp_file(self) -> dict[str, pd.DataFrame]:
        res = {}
        try:
            for id, file in enumerate(self.fileList):
                res[file] = pd.read_excel(
                    io=os.path.join(self.tmpDir, "LookupTable"), sheet_name=file
                ).apply(bw_unit_normalize, axis=1)
            return res
        except Exception:
            lTFile = fd.askopenfilename(
                title="Lookup Table File Not Found, Please Choose Lookup Table!",
                initialdir="~",
                filetypes=(
                    ("Excel Files", "*.xls *.xlsx *.xlsm *.xlsb"),
                    ("All Files", "*.*"),
                ),
            )
            if lTFile != "":
                os.makedirs(name=self.tmpDir, exist_ok=True)
                shutil.copy2(
                    src=Path(lTFile), dst=Path(os.path.join(self.tmpDir, "LookupTable"))
                )
                self.__temp_file()
            else:
                self.destroy()


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
