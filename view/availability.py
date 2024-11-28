from pathlib import Path
import customtkinter as ctk

import pandas as pd
from helper.ext_filehandler import ExtendedFileProcessor
from helper.readconfig import CopyLTFile, ReadLookupTable


class Availability(ctk.CTkFrame):
    lookupTableName = "Availability.lt"

    def __init__(self, master, controller):
        super().__init__(master=master)
        self.controller = controller
        self.rawData: dict[str, pd.DataFrame] = {}
        self.dir: Path = Path.home()
        self.init_view()

    def init_view(self):
        [item.destroy() for item in self.winfo_children()]
        try:
            self.lookUpTable = ReadLookupTable(
                filePath=self.controller.config.tmpDir.joinpath(self.lookupTableName)
            )
            self.inputFrame = ctk.CTkScrollableFrame(
                master=self, fg_color="transparent"
            )
            self.inputFrame.pack(fill=ctk.BOTH, expand=True)
            self.__input_forms()
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
