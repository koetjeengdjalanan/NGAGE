from pathlib import Path
import customtkinter as ctk
from tkinter.messagebox import Message

import pandas as pd
from helper.custom_widget import ListSelector
from helper.ext_filehandler import ExtendedFileProcessor
from helper.processing import count_by_column, count_occurrences
from helper.readconfig import CopyLTFile, GetConfigAsList, ReadLookupTable
from view.configtoplevel import ConfigTopLevel


class Availability(ctk.CTkFrame):
    lookupTableName = "Availability.lt"

    def __init__(self, master, controller):
        super().__init__(master=master)
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
        self.init_view()

    def init_view(self):
        [item.destroy() for item in self.winfo_children()]
        try:
            self.lookUpTable = ReadLookupTable(
                filePath=self.controller.config.tmpDir.joinpath(self.lookupTableName)
            )
            self.__input_forms()
            self.branchSetting = ListSelector(
                master=self,
                title="BSSB Settings",
                fg_color="transparent",
                items=self.branchList,
            )
            self.branchSetting.pack(fill=ctk.BOTH, expand=True, pady=10)
            self.__action_buttons()
            # if self.controller.env["DEV"]:
            #     self.insertOnDev()
        except FileNotFoundError:
            self.no_lt_view(reason="FileNotFoundError")
        except Exception as Error:
            raise Exception(Error)

    def no_lt_view(self, reason: str) -> None:
        def get_Lt():
            if CopyLTFile(self.lookupTableName) is not None:
                self.init_view()

        noLTFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        noLTFrame.pack(fill=ctk.BOTH, expand=True)
        noLTLabel = ctk.CTkLabel(
            master=noLTFrame, text=reason + "\nChoose Lookup Table!", font=("", 24)
        )
        noLTLabel.pack(fill=ctk.BOTH, expand=True)
        noLTFrame.bind(sequence="<1>", command=lambda x: get_Lt())
        noLTLabel.bind(sequence="<1>", command=lambda x: get_Lt())

    def insertOnDev(self):
        for each in self.lookUpTable.keys():
            if each not in self.controller.env["sourceFiles"]:
                continue
            print(f"assign: {each}")
            self.rawData[each] = {}
            for type in self.controller.env["sourceFiles"][each]:
                print(f"⊢→ {type}")
                match each:
                    case "F5":
                        pathInput = self.f5FilePathInput[type]
                    case "Firewall":
                        pathInput = self.firewallInputPath[type]
                    case _:
                        pathInput = self.inputFilePathInput[each][type]
                self.pick_file(
                    entry=pathInput,
                    name=each,
                    type=type,
                    filePath=Path(self.controller.env["sourceFiles"][each][type]),
                    isResource=False if "bw-" in type else True,
                )

    def __input_forms(self):
        self.inputFrame = ctk.CTkScrollableFrame(master=self, fg_color="transparent")
        self.inputFrame.pack(fill=ctk.BOTH, expand=True)
        self.inputFrame.columnconfigure(index=0, weight=1)
        self.inputFrame.columnconfigure(index=1, weight=2)
        ctk.CTkLabel(
            master=self.inputFrame, text="General Input Forms", font=("", 24)
        ).grid(column=0, row=0, sticky="nsew", padx=5, pady=10, columnspan=2)
        for row, each in enumerate(self.lookUpTable.keys(), start=1):
            ctk.CTkLabel(master=self.inputFrame, text=each).grid(
                column=0, row=row, sticky=ctk.W, padx=5, pady=5
            )
            ctk.CTkButton(
                master=self.inputFrame,
                text=f"Select {each} Files",
                cursor="hand2",
                command=lambda x=each, ro=row: self.pick_file(name=x, row=ro),
            ).grid(column=1, row=row, sticky=ctk.NSEW, padx=5, pady=5)

    def __action_buttons(self) -> None:
        def determineConfigWindow():
            try:
                if self.configTopLevel and self.configTopLevel.winfo_exists():
                    self.configTopLevel.focus()
                else:
                    raise AttributeError
            except AttributeError:
                self.configTopLevel = ConfigTopLevel(
                    master=self,
                    controller=self.controller,
                    configFormat=GetConfigAsList(
                        config=self.controller.config, section="fmt"
                    )["availability"],
                )
                self.configTopLevel.grab_set()

        actionButtonFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        actionButtonFrame.pack(fill=ctk.X, expand=False, padx=10, pady=10)
        ctk.CTkButton(
            master=actionButtonFrame, text="Confirm", command=self.process_data
        ).pack(side=ctk.RIGHT, ipadx=10)
        ctk.CTkButton(
            master=actionButtonFrame,
            text="Config",
            command=determineConfigWindow,
        ).pack(side=ctk.LEFT, ipadx=10)

    def pick_file(self, name: str, row: int) -> None:
        fileHandler = (
            ExtendedFileProcessor(initDir=self.dir).select_files(
                title=f"Select files for {name}"
            )
            # if filePath == ""
            # else ExtendedFileProcessor(initDir=self.dir, sourceFile=filePath)
        )
        sourceFiles = fileHandler.sourceFiles
        if sourceFiles is None:
            return None
        self.rawData[name] = fileHandler.sourceData
        if sourceFiles.__len__() != 0:
            self.rawData[name] = fileHandler.sourceData
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
                + "Do you want to save changes?",
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
            res[each] = count_occurrences(
                raw=self.rawData[each], lookupTable=self.lookUpTable[each]
            )
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
        extExcel = (
            ExtendedFileProcessor()
            .save_file_loc(dirStr=self.dir)
            .ext_export(
                data=res,
                rules=GetConfigAsList(config=self.controller.config, section="fmt")[
                    "availability"
                ],
                colList=self.branchSetting.get_items() + ["Count"],
            )
            .open_explorer()
        )
        print(extExcel.savedFile)
        self.controller.destroy()
