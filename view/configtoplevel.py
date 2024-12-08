import customtkinter as ctk

from pathlib import Path
from typing import Dict, List
from helper.getfile import GetFile


class ConfigTopLevel(ctk.CTkToplevel):
    def __init__(self, master, controller, configFormat: List[Dict]):
        super().__init__(master=master)
        self.title("Config")
        self.resizable(False, False)
        self.after(
            ms=250,
            func=lambda: self.iconbitmap(GetFile.getAssets(file_name="favicon.ico")),
        )
        self.controller = controller
        self.parent = master
        self.lookup_table_config()
        # self.cond_fmt_config()

    def lookup_table_config(self):
        def reset_lookup_table():
            Path.unlink(
                self.controller.config.tmpDir.joinpath(self.parent.lookupTableName)
            )
            self.parent.init_view()
            self.destroy()

        lookupTableConfigFrame = ctk.CTkFrame(master=self)
        lookupTableConfigFrame.pack(fill=ctk.X, expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            master=lookupTableConfigFrame, text="Lookup Table", font=("", 24)
        ).pack(pady=10)
        ctk.CTkButton(
            master=lookupTableConfigFrame,
            text="Delete Lookup Table",
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
        condFmtScrollableFrame.grid(sticky=ctk.NSEW)
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Criteria").grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5
        )
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Format").grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5
        )
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Value").grid(
            row=0, column=2, sticky="nsew", padx=5, pady=5
        )
        # for idx, key in enumerate(self.controller.config["cond_fmt"]):
        #     print(
        #         self.controller.config["cond_fmt"].get(key),
        #         type(self.controller.config["cond_fmt"].get(key)),
        #     )
        #     val = json_loads(
        #         self.controller.config["cond_fmt"].get(key).replace("'", '"')
        #     )
        #     ctk.CTkLabel(
        #         master=condFmtScrollableFrame,
        #         text=val["criteria"],
        #         font=("", 16),
        #     ).grid(row=idx + 1, column=0, sticky="nsew", padx=5, pady=2)
        #     ctk.CTkLabel(
        #         master=condFmtScrollableFrame,
        #         text=val["value"],
        #         font=("", 16),
        #     ).grid(row=idx + 1, column=1)


if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    ConfigTopLevel(root)
    root.mainloop()
