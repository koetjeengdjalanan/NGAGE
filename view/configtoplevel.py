import pandas as pd
import customtkinter as ctk

from pathlib import Path
from json import loads as json_loads
from helper.filehandler import FileHandler
from helper.getfile import GetFile
from helper.processing import bw_unit_normalize


class ConfigTopLevel(ctk.CTkToplevel):
    def __init__(self, master, controller):
        super().__init__(master=master)
        self.title("Config")
        self.resizable(False, False)
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.config = controller.config
        self.fileList: list[str] = controller.fileList
        print(Path(self.config.tmpDir, "LookupTable"))
        self.lookUpTable: dict[str, pd.DataFrame] = controller.lookUpTable
        self.lookup_table_config()
        # self.cond_fmt_config()

    def lookup_table_config(self):
        def reset_lookup_table():
            from shutil import copy2
            from tkinter.messagebox import showinfo

            self.withdraw()
            sourceFile = (
                FileHandler(initDir=Path.cwd())
                .select_file(title="Select Lookup Table")
                .sourceFile
            )
            if sourceFile is not None:
                for tower in self.fileList:
                    self.lookUpTable[tower] = pd.read_excel(
                        sourceFile, sheet_name=tower
                    )
                    self.lookUpTable[tower] = (
                        self.lookUpTable[tower].apply(bw_unit_normalize, axis=1)
                        if tower != self.fileList[-1]
                        else self.lookUpTable[tower]
                    )
                copy2(src=sourceFile, dst=Path(self.config.tmpDir, "LookupTable"))
            showinfo(title="Success", message="Lookup Table Updated Successfully!")
            self.deiconify()

        lookupTableConfigFrame = ctk.CTkFrame(master=self)
        lookupTableConfigFrame.pack(fill="x", expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            master=lookupTableConfigFrame, text="Lookup Table", font=("", 24)
        ).pack(pady=10)
        ctk.CTkButton(
            master=lookupTableConfigFrame,
            text="Change Lookup Table",
            command=reset_lookup_table,
        ).pack(pady=(0, 10))

    # TODO: Implement conditional formatting configuration
    def cond_fmt_config(self):
        condFmtConfigFrame = ctk.CTkFrame(master=self)
        condFmtConfigFrame.pack(fill="x", expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            master=condFmtConfigFrame, text="Conditional Formatting", font=("", 24)
        ).grid(pady=10)
        # critList: list[str] = ["=", "between", ">=", "<=", ">", "<"]
        condFmtScrollableFrame = ctk.CTkScrollableFrame(
            master=condFmtConfigFrame, fg_color="transparent"
        )
        condFmtScrollableFrame.grid(fill="both", expand=True)
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Criteria").grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5
        )
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Format").grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5
        )
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Value").grid(
            row=0, column=2, sticky="nsew", padx=5, pady=5
        )
        for idx, key in enumerate(self.config["cond_fmt"]):
            print(
                self.config["cond_fmt"].get(key), type(self.config["cond_fmt"].get(key))
            )
            val = json_loads(self.config["cond_fmt"].get(key).replace("'", '"'))
            ctk.CTkLabel(
                master=condFmtScrollableFrame,
                text=val["criteria"],
                font=("", 16),
            ).grid(row=idx + 1, column=0, sticky="nsew", padx=5, pady=2)
            # ctk.CTkLabel(
            #     master=condFmtScrollableFrame,
            #     text=val["value"],
            #     font=("", 16),
            # ).grid(row=idx + 1, column=1)


if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    ConfigTopLevel(root)
    root.mainloop()
