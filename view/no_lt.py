"""Fallback view renderer when no lookup table file is available.

Provide ``init_view``, which attempts to load a lookup-table Excel file
and build the normal input-form UI. If the file is missing, a clickable
placeholder is shown instead, prompting the user to select a lookup
table before proceeding.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

import customtkinter as ctk

from helper.readconfig import CopyLTFile, ReadLookupTable


def init_view(master, lookup_table_path: Path, views_func: Sequence[Callable[[], None]]) -> None:
    """Load a lookup table and build the view, or show a fallback prompt.

    Clear all existing child widgets from ``master``, then attempt to
    read the lookup table at ``lookup_table_path``. On success, store
    the parsed tables on ``master.lookUpTable``, create a scrollable
    input frame on ``master.inputFrame``, and invoke every function in
    ``views_func`` to populate the UI. On ``FileNotFoundError``, render
    a clickable placeholder that lets the user select a lookup table
    file.

    Args:
        master: The parent ``CTkFrame`` (e.g. ``Capacity`` or
            ``Availability``) whose children will be rebuilt.
        lookup_table_path (Path): Expected path to the lookup-table
            Excel file in the temp directory.
        views_func (Sequence[Callable[[], None]]): Ordered sequence of
            zero-argument callables that build the view's sub-sections
            (e.g. input forms, action buttons).
    """

    def no_lt_view(reason: str) -> None:
        """Render a clickable placeholder prompting the user to choose a lookup table.

        Display a centered label with the ``reason`` text and a
        "Choose Lookup Table!" call-to-action. Clicking anywhere on
        the frame opens the file dialog via ``CopyLTFile``.

        Args:
            reason (str): Short description of why the lookup table
                could not be loaded (e.g. ``"FileNotFoundError"``).
        """

        def get_Lt(*args, **kwargs):
            """Open the lookup-table file dialog and reinitialise the view."""
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
