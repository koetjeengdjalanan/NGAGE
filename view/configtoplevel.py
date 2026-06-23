"""Module for the configuration top-level window."""

from pathlib import Path

import customtkinter as ctk

from helper.getfile import GetFile
from models import Controller
from view.no_lt import init_view


class ConfigTopLevel(ctk.CTkToplevel):
    """Top-level configuration management window."""

    def __init__(self, master, controller: Controller, lt_table_name: str):
        super().__init__(master=master)
        self.title("Config")
        self.resizable(False, False)
        self.after(
            ms=250,
            func=lambda: GetFile.setIcon(self),
        )
        self.controller = controller
        self.lookupTableName = lt_table_name
        self.lookup_table_config()
        self.skip_lines_config()
        # self.cond_fmt_config()

    def lookup_table_config(self):
        """Build widgets for lookup table deletion and configuration."""

        def reset_lookup_table():
            Path.unlink(self.controller.config.tmpDir.joinpath(self.lookupTableName))
            init_view(
                master=self.master,
                lookup_table_path=self.controller.config.tmpDir.joinpath(self.lookupTableName),
                views_func=self.master.views_func,
            )
            self.destroy()

        lookupTableConfigFrame = ctk.CTkFrame(master=self)
        lookupTableConfigFrame.pack(fill=ctk.X, expand=True, padx=10, pady=10)
        ctk.CTkLabel(master=lookupTableConfigFrame, text="Lookup Table", font=("", 24)).pack(pady=10)
        ctk.CTkButton(
            master=lookupTableConfigFrame,
            text="Delete Lookup Table",
            command=reset_lookup_table,
        ).pack(pady=(0, 10))

    def skip_lines_config(self):
        """Set number of lines to be skipped."""

        def _validate_input_integer(char: str) -> bool:
            return any([char.isdigit(), char == ""])

        skip_line_vals = ctk.StringVar(value=str(self.controller.config.SKIP_ROWS))
        skip_line_config_frame = ctk.CTkFrame(master=self)
        skip_line_config_frame.pack(fill=ctk.X, expand=True, padx=10, pady=10)
        ctk.CTkLabel(master=skip_line_config_frame, text="Skip Lines", font=("", 24)).pack(pady=10)

        skip_line_entry = ctk.CTkEntry(
            master=skip_line_config_frame,
            textvariable=skip_line_vals,
            placeholder_text="Number of lines to skip",
            validate="key",
            validatecommand=(skip_line_config_frame.register(_validate_input_integer), "%S"),
        )
        skip_line_entry.pack(pady=10, padx=10)
        skip_line_entry.bind(
            "<Return>",
            lambda e: self.controller.config.set(
                section="preamble", option="skip_rows", value=str(skip_line_vals.get())
            ),
        )
        skip_line_entry.bind(
            "<MouseWheel>",
            lambda e: skip_line_vals.set(str(max(0, int(skip_line_vals.get() or 0) + (1 if e.delta > 0 else -1)))),
        )
        ctk.CTkButton(
            master=skip_line_config_frame,
            text="Save",
            command=lambda: self.controller.config.set(
                section="preamble", option="skip_rows", value=str(skip_line_vals.get())
            ),
        ).pack(pady=10, padx=10)

    # TODO: Implement conditional formatting configuration
    def cond_fmt_config(self):
        """Configure conditional formatting parameters."""
        condFmtConfigFrame = ctk.CTkFrame(master=self)
        condFmtConfigFrame.pack(fill="x", expand=True, padx=10, pady=10)
        ctk.CTkLabel(master=condFmtConfigFrame, text="Conditional Formatting", font=("", 24)).grid(pady=10)
        # critList: list[str] = ["=", "between", ">=", "<=", ">", "<"]
        condFmtScrollableFrame = ctk.CTkScrollableFrame(master=condFmtConfigFrame, fg_color="transparent")
        condFmtScrollableFrame.grid(sticky=ctk.NSEW)
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Criteria").grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5
        )
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Format").grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(master=condFmtScrollableFrame, text="Value").grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
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
