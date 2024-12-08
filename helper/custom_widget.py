import customtkinter as ctk
from typing import Any, LiteralString, Tuple, List


class ListSelector(ctk.CTkFrame):
    """
    A custom frame for displaying a list of items with checkboxes.
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
        title: LiteralString | None = "List Selector",
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
        self.itemsVar: List[ctk.BooleanVar] = [
            ctk.BooleanVar(master=self, name=item, value=True) for item in items
        ]
        self.searchVal = ctk.StringVar(master=self, name="searchVal")
        self.__search_bar()
        self.__init_populate()

    def __init_populate(self):
        self.listbox = ctk.CTkScrollableFrame(master=self)
        self.listbox.pack(fill=ctk.BOTH, expand=True)
        for item in self.itemsVar:
            _ = ctk.CTkFrame(master=self.listbox, bg_color="transparent")
            _.pack(fill=ctk.X, pady=3)
            ctk.CTkCheckBox(master=_, variable=item, text=item._name).pack(
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
            __.bind("<Button-1>", lambda x=item: self.remove_items(item))
            __.pack(side=ctk.RIGHT, ipadx=10)

    def remove_items(self, item):
        self.itemsVar.remove(item)
        self.repopulate_checklist()

    def repopulate_checklist(self, *args, **kwargs):
        [x.destroy() for x in self.listbox.winfo_children()]
        for item in self.itemsVar:
            if self.searchVal.get().lower() not in item._name.lower():
                continue
            _ = ctk.CTkFrame(master=self.listbox, bg_color="transparent")
            _.pack(fill=ctk.X, pady=3)
            ctk.CTkCheckBox(master=_, variable=item, text=item._name).pack(
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
            __.bind("<Button-1>", lambda x=item: self.remove_items(item))
            __.pack(side=ctk.RIGHT, ipadx=10)

    def __search_bar(self):
        def add_to_list():
            self.itemsVar.append(
                ctk.BooleanVar(
                    master=self, name=self.searchVal.get().strip(), value=True
                )
            )
            self.repopulate_checklist()
            check_if_exists()

        def check_if_exists(*args, **kwargs):
            if self.searchVal.get().strip() in [item._name for item in self.itemsVar]:
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
        """
        Retrieve the selected items from the ListSelector.

        This method returns a list of strings representing the names of the items
        that have been selected (checked) in the ListSelector widget.

        Returns:
            List[str]: A list containing the names of the selected items. If no items
            are selected, an empty list is returned.
        """
        return [item._name for item in self.itemsVar if item.get()]
