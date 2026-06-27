"""Custom CustomTkinter widgets for interactive list selection.

Provide ``ItemState`` for tracking individual checkbox state and
``ListSelector``, a composite frame that renders a searchable,
scrollable checklist with add and remove capabilities.
"""

from typing import Any, List, Tuple

import customtkinter as ctk


class ItemState:
    """Track the checked state of a single item in a ``ListSelector``.

    Attributes:
        name (str): The display name of the item.
        var (ctk.BooleanVar): Tkinter boolean variable bound to the
            item's checkbox, ``True`` when checked.
    """

    def __init__(self, name: str, var: ctk.BooleanVar):
        """Initialize an item with a display name and a boolean variable.

        Args:
            name (str): The display name of the item shown next to its
                checkbox.
            var (ctk.BooleanVar): The Tkinter boolean variable that
                tracks whether this item is checked.
        """
        self.name = name
        self.var = var


class ListSelector(ctk.CTkFrame):
    """Searchable checklist frame with add and remove capabilities.

    Render a titled frame containing a search bar, an "Add" button, and
    a scrollable list of checkboxes. Users can filter items by typing in
    the search bar, add new items that do not already exist, remove
    existing items via a clickable label, and toggle individual items
    on or off.

    Attributes:
        itemsVar (list[ItemState]): The current list of items and their
            checked states.
        searchVal (ctk.StringVar): The current search-bar text, used to
            filter the displayed checklist.
        listbox (ctk.CTkScrollableFrame): The scrollable container that
            holds the rendered checkbox rows.
    """

    def __init__(
        self,
        master: Any,
        width: int = 200,
        height: int = 200,
        corner_radius: int | str | None = None,
        border_width: int | str | None = None,
        bg_color: str | Tuple[str, str] = "transparent",
        fg_color: str | Tuple[str, str] | None = None,
        border_color: str | Tuple[str, str] | None = None,
        background_corner_colors: Tuple[str | Tuple[str, str]] | None = None,
        overwrite_preferred_drawing_method: str | None = None,
        title: str = "List Selector",
        items: List[str] = [],
        **kwargs,
    ):
        super().__init__(
            master=master,
            width=width,
            height=height,
            corner_radius=corner_radius,
            border_width=border_width,
            bg_color=bg_color,
            fg_color=fg_color,
            border_color=border_color,
            background_corner_colors=background_corner_colors,
            overwrite_preferred_drawing_method=overwrite_preferred_drawing_method,
            **kwargs,
        )
        ctk.CTkLabel(master=self, text=title, font=("", 14)).pack(
            fill=ctk.X, padx=5, pady=5
        )
        self.itemsVar: List[ItemState] = [
            ItemState(item, ctk.BooleanVar(master=self, value=True)) for item in items
        ]
        self.searchVal = ctk.StringVar(master=self, name="searchVal")
        self.__search_bar()
        self.__init_populate()

    def __init_populate(self):
        """Build the initial scrollable checklist from ``itemsVar``.

        Create a ``CTkScrollableFrame`` and populate it with one row per
        item, each containing a checkbox and a clickable "remove" label.
        """
        self.listbox = ctk.CTkScrollableFrame(master=self)
        self.listbox.pack(fill=ctk.BOTH, expand=True)
        for item in self.itemsVar:
            _ = ctk.CTkFrame(master=self.listbox, bg_color="transparent")
            _.pack(fill=ctk.X, pady=3)
            ctk.CTkCheckBox(master=_, variable=item.var, text=item.name).pack(
                fill=ctk.X, side=ctk.LEFT
            )
            __ = ctk.CTkLabel(
                master=_,
                text="remove",
                text_color="gray",
                font=ctk.CTkFont(slant="italic", size=10),
                cursor="hand2",
            )
            __.bind(
                "<Enter>", lambda e, label=__: label.configure(text_color="deeppink")
            )
            __.bind("<Leave>", lambda e, label=__: label.configure(text_color="gray"))
            __.bind("<Button-1>", lambda e, x=item: self.remove_items(x))
            __.pack(side=ctk.RIGHT, ipadx=10)

    def remove_items(self, item: ItemState) -> None:
        """Remove an item from the checklist and refresh the display.

        Args:
            item (ItemState): The ``ItemState`` instance to remove from
                the internal item list.
        """
        self.itemsVar.remove(item)
        self.repopulate_checklist()

    def repopulate_checklist(self, *args, **kwargs) -> None:
        """Rebuild the visible checklist, applying the current search filter.

        Destroy all existing child widgets inside the scrollable frame
        and re-create checkbox rows only for items whose names contain
        the current ``searchVal`` substring (case-insensitive). This
        method is called automatically whenever the search text changes
        and after an item is added or removed.
        """
        [x.destroy() for x in self.listbox.winfo_children()]
        for item in self.itemsVar:
            if self.searchVal.get().lower() not in item.name.lower():
                continue
            _ = ctk.CTkFrame(master=self.listbox, bg_color="transparent")
            _.pack(fill=ctk.X, pady=3)
            ctk.CTkCheckBox(master=_, variable=item.var, text=item.name).pack(
                fill=ctk.X, side=ctk.LEFT
            )
            __ = ctk.CTkLabel(
                master=_,
                text="remove",
                text_color="gray",
                font=ctk.CTkFont(slant="italic", size=10),
                cursor="hand2",
            )
            __.bind(
                "<Enter>", lambda e, label=__: label.configure(text_color="deeppink")
            )
            __.bind("<Leave>", lambda e, label=__: label.configure(text_color="gray"))
            __.bind("<Button-1>", lambda e, x=item: self.remove_items(x))
            __.pack(side=ctk.RIGHT, ipadx=10)

    def __search_bar(self):
        """Build the search bar frame with a text entry and an "Add" button.

        Wire the search entry's ``trace_add`` callback to
        ``repopulate_checklist`` so the checklist filters in real time.
        The "Add" button is enabled only when the search text is
        non-empty and does not match an existing item name.
        """
        def add_to_list():
            self.itemsVar.append(
                ItemState(
                    self.searchVal.get().strip(),
                    ctk.BooleanVar(master=self, value=True)
                )
            )
            self.repopulate_checklist()
            check_if_exists()

        def check_if_exists(*args, **kwargs):
            if self.searchVal.get().strip() in [item.name for item in self.itemsVar]:
                addButton.configure(text="Existed!", state=ctk.DISABLED)
            elif self.searchVal.get().strip() == "":
                addButton.configure(text="Add", state=ctk.DISABLED)
            else:
                addButton.configure(text="Add", state=ctk.NORMAL)

        searchBarFrame = ctk.CTkFrame(master=self, bg_color="transparent")
        searchBarFrame.pack(fill=ctk.X, ipadx=5, pady=5)
        searchBarFrame.columnconfigure(1, weight=3)
        ctk.CTkLabel(master=searchBarFrame, text="Search:").grid(
            row=0, column=0, padx=5, pady=5
        )
        searchBar = ctk.CTkEntry(
            master=searchBarFrame,
            textvariable=self.searchVal,
        )
        searchBar.grid(row=0, column=1, padx=5, pady=5, sticky=ctk.EW)
        addButton = ctk.CTkButton(
            master=searchBarFrame, text="Add", state=ctk.DISABLED, command=add_to_list
        )
        addButton.grid(row=0, column=2, padx=5, pady=5)
        self.searchVal.trace_add("write", self.repopulate_checklist)
        self.searchVal.trace_add("write", check_if_exists)

    def get_items(self) -> List[str]:
        """Return the names of all currently checked items.

        Iterate over ``itemsVar`` and collect the ``name`` of every
        ``ItemState`` whose ``var`` is ``True``.

        Returns:
            List[str]: A list of item names that are currently checked.
                An empty list is returned when no items are selected.
        """
        return [item.name for item in self.itemsVar if item.var.get()]
