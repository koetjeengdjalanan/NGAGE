"""Collection of function to render default view if no lookup table is found."""

from collections.abc import Callable, Sequence
from pathlib import Path

import customtkinter as ctk

from helper.readconfig import CopyLTFile, ReadLookupTable


def init_view(master, lookup_table_path: Path, views_func: Sequence[Callable[[], None]]) -> None:
    """Initialize the Capacity view by building the input forms and action buttons."""

    def no_lt_view(reason: str) -> None:
        """Display placeholder view when lookup table file is missing.

        Args:
            reason (str): Reason description.
        """

        def get_Lt(*args, **kwargs):
            if CopyLTFile(lookup_table_path.name) is not None:
                init_view(master, lookup_table_path, views_func)

        noLTFrame = ctk.CTkFrame(
            master=master,
            fg_color="transparent",
            cursor="hand2",
        )
        noLTFrame.pack(fill=ctk.BOTH, expand=True)
        noLTLabel = ctk.CTkLabel(
            master=noLTFrame,
            text=reason + "\nChoose Lookup Table!",
            font=("", 24),
            cursor="hand2",
        )
        noLTLabel.pack(fill=ctk.BOTH, expand=True)
        noLTFrame.bind(sequence="<1>", command=get_Lt)
        noLTLabel.bind(sequence="<1>", command=get_Lt)

    [item.destroy() for item in master.winfo_children()]
    try:
        master.lookUpTable = ReadLookupTable(filePath=lookup_table_path)
        master.inputFrame = ctk.CTkScrollableFrame(master=master, fg_color="transparent")
        master.inputFrame.pack(fill=ctk.BOTH, expand=True)
        [func() for func in views_func]
    except FileNotFoundError:
        no_lt_view(reason="FileNotFoundError")
    except Exception as Error:
        raise Exception(Error)
