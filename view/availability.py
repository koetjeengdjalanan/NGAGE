"""Availability analysis tab for counting interface-down events.

Provide the ``Availability`` frame that lets the user select syslog CSV
exports, configure BSSB branch hostnames, and compute per-interface
down-event counts against a lookup table. Results are exported to an
Excel file with conditional formatting.
"""

from pathlib import Path
from tkinter.messagebox import Message

import customtkinter as ctk
import pandas as pd

from helper.custom_widget import ListSelector
from helper.ext_filehandler import ExtendedFileProcessor
from helper.processing import count_by_column, count_occurrences
from helper.readconfig import GetConfigAsList
from models import Controller
from view.configtoplevel import ConfigTopLevel
from view.no_lt import init_view


class Availability(ctk.CTkFrame):
    """UI frame for the Availability analysis tab.

    Display a branch-settings checklist, dynamically generated input
    forms (one per lookup-table sheet), and Confirm/Config action
    buttons. On confirmation, process the selected syslog files to
    count interface-down events and export the results to Excel.

    Attributes:
        lookupTableName (str): File name used to cache the Availability
            lookup table in the temp directory.
        controller (Controller): Shared application controller.
        rawData (dict[str, pd.DataFrame]): Mapping of sheet names to
            user-selected syslog DataFrames.
        dir (Path): Last-used directory for file dialogs.
        branchList (list[str]): BSSB hostnames loaded from config.
        configTopLevel (ConfigTopLevel | None): Reference to the open
            config dialog, or ``None``.
        views_func (list[Callable]): Ordered list of view-builder
            callables invoked by ``init_view``.
    """

    lookupTableName = "Availability.lt"

    def __init__(self, master: ctk.CTkFrame, controller: Controller):
        super().__init__(master=master)
        self._name = "Availability"
        self.controller = controller
        self.rawData: dict[str, pd.DataFrame] = {}
        self.dir: Path = Path.home()
        self.branchList: list[str] = list(
            self.controller.config.get(
                "availability",
                "bssb_list",
                fallback="idjktpdc01extwr05,idjktpdc01extwr06,idjktpdc01extwr08,idjktsdc03extwr05,idjktsdc03extwr06,idjktsdc03extwr08",
            ).split(",")
        )
        self.configTopLevel = None
        self.views_func = [self.__setup_branch_settings, self.__input_forms, self.__action_buttons]
        self.inputFrame: ctk.CTkScrollableFrame
        self.lookUpTable: dict[str, pd.DataFrame]
        init_view(
            master=self,
            lookup_table_path=self.controller.config.tmpDir.joinpath(self.lookupTableName),
            views_func=self.views_func,
        )

    def __setup_branch_settings(self) -> None:
        """Build the BSSB branch-settings checklist.

        Instantiate a ``ListSelector`` pre-populated with the hostname
        list from the application config and pack it into the frame.
        The user can search, add, remove, or toggle individual branch
        hostnames.
        """
        self.branchSetting = ListSelector(
            master=self,
            title="BSSB Settings",
            fg_color="transparent",
            items=self.branchList,
        )
        self.branchSetting.pack(fill=ctk.BOTH, expand=True, pady=10)

    def __input_forms(self):
        """Build the input-form grid for selecting syslog files.

        Create one row per lookup-table sheet with a label and a button
        that opens a multi-file selection dialog. The grid is rendered
        inside the shared scrollable ``inputFrame``.
        """
        # self.inputFrame = ctk.CTkScrollableFrame(master=self, fg_color="transparent")
        # self.inputFrame.pack(fill=ctk.BOTH, expand=True)
        self.inputFrame.columnconfigure(index=0, weight=1)
        self.inputFrame.columnconfigure(index=1, weight=2)
        ctk.CTkLabel(master=self.inputFrame, text="General Input Forms", font=("", 24)).grid(
            column=0, row=0, sticky="nsew", padx=5, pady=10, columnspan=2
        )
        for row, each in enumerate(self.lookUpTable.keys(), start=1):
            ctk.CTkLabel(master=self.inputFrame, text=each).grid(column=0, row=row, sticky=ctk.W, padx=5, pady=5)
            ctk.CTkButton(
                master=self.inputFrame,
                text=f"Select {each} Files",
                cursor="hand2",
                command=lambda x=each, ro=row: self.pick_file(name=x, row=ro),
            ).grid(column=1, row=row, sticky=ctk.NSEW, padx=5, pady=5)

    def __action_buttons(self) -> None:
        """Build the Confirm and Config action buttons.

        The **Confirm** button triggers ``process_data``. The **Config**
        button opens (or focuses) the ``ConfigTopLevel`` dialog for
        managing the lookup table and skip-rows settings.
        """
        def determineConfigWindow():
            try:
                if self.configTopLevel and self.configTopLevel.winfo_exists():
                    self.configTopLevel.focus()
                else:
                    raise AttributeError
            except AttributeError:
                config_list = GetConfigAsList(config=self.controller.config, section="fmt")["availability"]
                if not isinstance(config_list, list):
                    config_list = []
                self.configTopLevel = ConfigTopLevel(
                    master=self, controller=self.controller, lt_table_name=self.lookupTableName
                )
                self.configTopLevel.wait_visibility()
                self.configTopLevel.grab_set()

        actionButtonFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        actionButtonFrame.pack(fill=ctk.X, expand=False, padx=10, pady=10)
        ctk.CTkButton(master=actionButtonFrame, text="Confirm", command=self.process_data).pack(
            side=ctk.RIGHT, ipadx=10
        )
        ctk.CTkButton(
            master=actionButtonFrame,
            text="Config",
            command=determineConfigWindow,
        ).pack(side=ctk.LEFT, ipadx=10)

    def pick_file(self, name: str, row: int) -> None:
        """Open a multi-file dialog and load syslog CSVs for a device category.

        Present a file dialog for the user to select one or more CSV
        files. The selected files are concatenated and stored in
        ``self.rawData[name]``. The button in the input-form grid at
        ``row`` is replaced with a frame listing the selected file
        names.

        Args:
            name (str): Lookup-table sheet name identifying the device
                category (e.g. ``"BSSB"``).
            row (int): Grid row index of the button to replace with
                file-name labels.
        """
        fileHandler = ExtendedFileProcessor(initDir=self.dir).select_files(title=f"Select files for {name}")
        sourceFiles = fileHandler.sourceFiles
        if sourceFiles is None:
            return None
        source_data = fileHandler.sourceData
        if source_data is None:
            return None
        if len(sourceFiles) != 0:
            self.rawData[name] = source_data
            self.dir = sourceFiles[0].parent.absolute()
            button = self.inputFrame.grid_slaves(row=row, column=1)[0]
            wid = button.winfo_width()
            button.destroy()
            _ = ctk.CTkFrame(master=self.inputFrame, width=wid, border_width=1)
            _.grid_propagate(False)
            _.grid(column=1, row=row, sticky=ctk.NSEW, padx=5, pady=5)
            for sourceFile in sourceFiles:
                ctk.CTkLabel(
                    master=_,
                    text=str(sourceFile.name),
                    wraplength=wid,
                    anchor=ctk.E,
                ).pack(fill=ctk.NONE, expand=False)

    def check_integrity(self) -> bool:
        """Validate branch-settings changes and optionally persist them.

        Compare the current ``ListSelector`` items against the stored
        ``branchList``. If items were added or removed and BSSB data has
        been loaded, prompt the user with a yes/no/cancel dialog. On
        "yes", save the updated list to the config. On "cancel", abort
        processing.

        Returns:
            bool: ``True`` if processing should continue, ``False`` if
                the user cancelled.
        """
        confirmDataChanges: str = "unbounded"
        added = set(self.branchSetting.get_items()) - set(self.branchList)
        removed = set(self.branchList) - set(self.branchSetting.get_items())
        if "BSSB" in self.rawData.keys() and (added or removed):
            confirmDataChanges = Message(
                master=self,
                title="Data Integrity Failed!",
                detail="There is new item(s) appended to the branch setting list",
                message="This key(s) has been\n"
                + (f"Added {added} " if added else "")
                + (f"Removed {removed} " if removed else "")
                + "\nDo you want to save changes?",
                icon="warning",
                type="yesnocancel",
                default="no",
            ).show()
            if confirmDataChanges == "yes":
                self.controller.config.set(
                    "availability",
                    "bssb_list",
                    ",".join(self.branchSetting.get_items()),
                )
                self.controller.config.write_config()
        return False if confirmDataChanges == "cancel" else True

    def process_data(self) -> None:
        """Run the availability analysis pipeline and export results.

        Iterate over each lookup-table sheet, count interface-down
        events from the corresponding syslog data (using
        ``count_occurrences`` or ``count_by_column`` for BSSB sheets),
        warn about any missing inputs, and export the results to a
        conditionally-formatted Excel file. The file explorer is opened
        on completion and the application window is destroyed.
        """
        if not self.check_integrity():
            return None
        skip: list[str] = []
        res: dict[str, pd.DataFrame] = {}
        for each in self.lookUpTable.keys():
            if each not in self.rawData.keys():
                skip.append(each)
                continue
            if each.lower() in "bssb":
                res[each] = count_by_column(
                    raw=self.rawData[each],
                    lookupTable=self.lookUpTable[each],
                    columnList=self.branchSetting.get_items(),
                )
                continue
            res[each] = count_occurrences(raw=self.rawData[each], lookupTable=self.lookUpTable[each])
        if skip.__len__() != 0:
            Message(
                master=self,
                title="Missing Value",
                detail="Some data not found!",
                icon="warning",
                type="ok",
                default="ok",
                message=f"The following keys are not found in the raw data: {skip}",
            ).show()
        extExcel = ExtendedFileProcessor()
        extExcel.save_file_loc(dirStr=self.dir)
        rules_list = GetConfigAsList(config=self.controller.config, section="fmt")["availability"]
        if not isinstance(rules_list, list):
            rules_list = []
        extExcel.ext_export(
            data=res,
            rules=rules_list,
            colList=self.branchSetting.get_items() + ["Count"],
        )
        extExcel.open_explorer()
        print(extExcel.savedFile)
        self.controller.root.destroy()
