"""Top-level configuration window for managing lookup tables and skip-line settings.

Provide ``ConfigTopLevel``, a ``CTkToplevel`` dialog that lets the user
delete the cached lookup table (triggering a re-prompt) and adjust the
number of header rows to skip when reading CSV files.
"""

from pathlib import Path

import customtkinter as ctk

from helper.getfile import GetFile
from models import Controller
from view.no_lt import init_view


class ConfigTopLevel(ctk.CTkToplevel):
    """Modal configuration dialog for runtime settings.

    Present a non-resizable top-level window with sections for deleting
    the cached lookup table and configuring the CSV skip-rows value.
    The window grabs focus so the user must close it before returning
    to the main application.

    Attributes:
        controller (Controller): Shared application controller providing
            access to ``AppConfig`` and ``Environment``.
        lookupTableName (str): File name of the lookup table managed by
            this config dialog (e.g. ``"Capacity.lt"``).
    """

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
        """Build the lookup-table management section.

        Render a frame with a "Delete Lookup Table" button. When
        clicked, the cached lookup-table file is removed from the temp
        directory and the parent view is re-initialised via
        ``init_view``, which will show the fallback file-selection
        prompt. This dialog is then destroyed.
        """

        def reset_lookup_table():
            Path.unlink(self.controller.config.tmpDir.joinpath(self.lookupTableName))
            init_view(
                master=self.master,
                lookup_table_path=self.controller.config.tmpDir.joinpath(self.lookupTableName),
                views_func=getattr(self.master, "views_func", []),
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
        """Build the skip-lines configuration section.

        Render a frame with a numeric entry field and a "Save" button.
        The entry accepts only non-negative integers and supports mouse-
        wheel scrolling to increment or decrement the value. Pressing
        Enter or clicking "Save" persists the value to the ``preamble``
        section of the application config.
        """

        def _validate_input_integer(char: str) -> bool:
            return any([char.isdigit(), char == ""])

        def _save_skip_rows():
            value = str(skip_line_vals.get())
            self.controller.config.set(section="preamble", option="skip_rows", value=value)
            self.controller.config.SKIP_ROWS = int(value)
            self.controller.config.write_config()
            self.destroy()

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
            lambda e: _save_skip_rows(),
        )
        def _handle_scroll(event):
            try:
                current_val = int(skip_line_vals.get() or 0)
            except ValueError:
                current_val = 0

            delta = 1 if getattr(event, "delta", 0) > 0 else -1
            skip_line_vals.set(str(max(0, current_val + delta)))
            return "break"

        skip_line_entry.bind("<MouseWheel>", _handle_scroll)
        ctk.CTkButton(
            master=skip_line_config_frame,
            text="Save",
            command=_save_skip_rows,
        ).pack(pady=10, padx=10)

    # TODO: Implement conditional formatting configuration
    def cond_fmt_config(self):
        """Build the conditional-formatting configuration section.

        Render a scrollable frame intended to display and edit the
        conditional-format rules (criteria, format, value). This section
        is currently a work-in-progress and its body is commented out.
        """
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
