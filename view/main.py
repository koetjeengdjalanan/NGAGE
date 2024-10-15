from pathlib import Path
import tkinter
import tkinter.messagebox
import customtkinter as ctk
import pandas as pd

from helper.ext_excel import ExtendedExcelProcessor
from helper.processing import (
    bw_unit_normalize,
    conc_df,
    process_basic,
    process_f5,
    process_firewall,
    process_with_from_n_to,
)
from helper.filehandler import FileHandler
from view.configtoplevel import ConfigTopLevel


class MainView(ctk.CTkFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master=master, fg_color="transparent", corner_radius=None)
        self.inputFrame = ctk.CTkScrollableFrame(master=self, fg_color="transparent")
        self.inputFrame.pack(fill=ctk.BOTH, expand=True)
        self.controller = controller
        self.dir: str = Path().cwd()
        self.inputList: list[str] = controller.fileList[:-2]
        self.rawData: dict[str, dict[str, pd.DataFrame]] = {}
        self.configTopLevel = None
        self.__general_input_forms()
        self.__fFive_input_forms()
        self.__firewall_input_forms()
        self.__action_button()
        if self.controller.env["DEV"]:
            self.insertOnDev()

    def insertOnDev(self):
        for each in self.controller.env["sourceFiles"]:
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

    # TODO: Refactor this method to be more readable & reuseable
    def __general_input_forms(self) -> None:
        ### General Inputs Forms
        self.inputFilePathInput: dict[str, dict[str, ctk.CTkEntry]] = {}
        inputFormsFrame = ctk.CTkFrame(master=self.inputFrame)
        inputFormsFrame.pack(fill=ctk.BOTH, expand=False, padx=10, pady=10)
        inputFormsFrame.columnconfigure(index=0, weight=1)
        inputFormsFrame.columnconfigure(index=1, weight=3)
        inputFormsFrame.columnconfigure(index=2, weight=3)
        ctk.CTkLabel(
            master=inputFormsFrame, text="Bandwidths In-Out", font=("", 24)
        ).grid(column=0, row=0, sticky="nsew", padx=5, pady=10, columnspan=3)
        ctk.CTkLabel(master=inputFormsFrame, text="Bandwidth In").grid(
            column=1, row=1, sticky="nsew", padx=5, pady=5
        )
        ctk.CTkLabel(master=inputFormsFrame, text="Bandwidth Out").grid(
            column=2, row=1, sticky="nsew", padx=5, pady=5
        )
        inputFormsFrame.columnconfigure(index=2, weight=3)
        for id, input in enumerate(iterable=self.inputList, start=2):
            ctk.CTkLabel(master=inputFormsFrame, text=input).grid(
                column=0, row=id, sticky=ctk.W, padx=5, pady=5
            )
            self.inputFilePathInput[input] = {}
            self.inputFilePathInput[input]["bw-in"] = ctk.CTkEntry(
                master=inputFormsFrame, state=ctk.DISABLED
            )
            self.inputFilePathInput[input]["bw-in"].grid(
                column=1, row=id, sticky="nsew", padx=5, pady=5
            )
            self.inputFilePathInput[input]["bw-in"].bind(
                "<1>",
                lambda event, x=input: self.pick_file(
                    entry=self.inputFilePathInput[x]["bw-in"], name=x, type="bw-in"
                ),
            )
            self.inputFilePathInput[input]["bw-out"] = ctk.CTkEntry(
                master=inputFormsFrame, state=ctk.DISABLED
            )
            self.inputFilePathInput[input]["bw-out"].grid(
                column=2, row=id, sticky="nsew", padx=5, pady=5
            )
            self.inputFilePathInput[input]["bw-out"].bind(
                "<1>",
                lambda event, x=input: self.pick_file(
                    entry=self.inputFilePathInput[x]["bw-out"], name=x, type="bw-out"
                ),
            )

    # TODO: Refactor this method to be more readable & reuseable
    def __fFive_input_forms(self) -> None:
        ### F5 Input Forms
        self.f5FilePathInput: dict[str, str | None] = {
            "bw-in": None,
            "bw-out": None,
            "pdc-cpu": None,
            "sdc-cpu": None,
            "mem": None,
        }
        f5FormsFrame = ctk.CTkFrame(master=self.inputFrame)
        f5FormsFrame.pack(fill=ctk.BOTH, expand=False, padx=10, pady=10)
        f5FormsFrame.columnconfigure(0, weight=1)
        f5FormsFrame.columnconfigure(1, weight=1)
        ctk.CTkLabel(master=f5FormsFrame, text="F5 Forms Inputs", font=("", 24)).grid(
            column=0, row=0, sticky="nsew", padx=5, pady=10, columnspan=2
        )
        ctk.CTkLabel(master=f5FormsFrame, text="Bandwidth In").grid(
            column=0, row=1, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.f5FilePathInput["bw-in"] = ctk.CTkEntry(
            master=f5FormsFrame, state=ctk.DISABLED
        )
        self.f5FilePathInput["bw-in"].grid(
            column=0, row=2, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.f5FilePathInput["bw-in"].bind(
            "<1>",
            lambda event, x="bw-in": self.pick_file(
                entry=self.f5FilePathInput[x], name="F5", type=x
            ),
        )
        ctk.CTkLabel(master=f5FormsFrame, text="Bandwidth Out").grid(
            column=1, row=1, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.f5FilePathInput["bw-out"] = ctk.CTkEntry(
            master=f5FormsFrame, state=ctk.DISABLED
        )
        self.f5FilePathInput["bw-out"].grid(
            column=1, row=2, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.f5FilePathInput["bw-out"].bind(
            "<1>",
            lambda event, x="bw-out": self.pick_file(
                entry=self.f5FilePathInput[x], name="F5", type=x
            ),
        )
        ctk.CTkLabel(master=f5FormsFrame, text="PDC CPU 95th %").grid(
            column=0, row=3, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.f5FilePathInput["pdc-cpu"] = ctk.CTkEntry(
            master=f5FormsFrame, state=ctk.DISABLED
        )
        self.f5FilePathInput["pdc-cpu"].grid(
            column=0, row=4, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.f5FilePathInput["pdc-cpu"].bind(
            "<1>",
            lambda event, x="pdc-cpu": self.pick_file(
                entry=self.f5FilePathInput[x], name="F5", type=x, isResource=True
            ),
        )
        ctk.CTkLabel(master=f5FormsFrame, text="SDC CPU 95th %").grid(
            column=1, row=3, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.f5FilePathInput["sdc-cpu"] = ctk.CTkEntry(
            master=f5FormsFrame, state=ctk.DISABLED
        )
        self.f5FilePathInput["sdc-cpu"].grid(
            column=1, row=4, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.f5FilePathInput["sdc-cpu"].bind(
            "<1>",
            lambda event, x="sdc-cpu": self.pick_file(
                entry=self.f5FilePathInput[x], name="F5", type=x, isResource=True
            ),
        )
        ctk.CTkLabel(master=f5FormsFrame, text="Mem 95th %").grid(
            column=0, row=5, sticky="nsew", padx=5, pady=(5, 0), columnspan=2
        )
        self.f5FilePathInput["mem"] = ctk.CTkEntry(
            master=f5FormsFrame, state=ctk.DISABLED
        )
        self.f5FilePathInput["mem"].grid(
            column=0, row=6, sticky="nsew", padx=5, pady=(0, 5), columnspan=2
        )
        self.f5FilePathInput["mem"].bind(
            "<1>",
            lambda event, x="mem": self.pick_file(
                entry=self.f5FilePathInput[x], name="F5", type=x, isResource=True
            ),
        )

    # TODO: Refactor this method to be more readable & reuseable
    def __firewall_input_forms(self) -> None:
        ### Firewall Input Forms
        self.firewallInputPath: dict[str, str | None] = {
            "cpu": None,
            "mem": None,
            "con-cp": None,
            "con-noncp": None,
        }
        firewallFormsFrame = ctk.CTkFrame(master=self.inputFrame)
        firewallFormsFrame.pack(fill=ctk.BOTH, expand=False, padx=10, pady=10)
        firewallFormsFrame.columnconfigure(0, weight=1)
        firewallFormsFrame.columnconfigure(1, weight=1)
        ctk.CTkLabel(
            master=firewallFormsFrame, text="Firewall Forms Inputs", font=("", 24)
        ).grid(column=0, row=0, sticky="nsew", padx=5, pady=10, columnspan=2)
        ctk.CTkLabel(master=firewallFormsFrame, text="CPU").grid(
            column=0, row=1, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.firewallInputPath["cpu"] = ctk.CTkEntry(
            master=firewallFormsFrame, state=ctk.DISABLED
        )
        self.firewallInputPath["cpu"].grid(
            column=0, row=2, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.firewallInputPath["cpu"].bind(
            "<1>",
            lambda event, x="cpu": self.pick_file(
                entry=self.firewallInputPath[x],
                name="Firewall",
                type=x,
                isResource=True,
            ),
        )
        ctk.CTkLabel(master=firewallFormsFrame, text="Mem").grid(
            column=1, row=1, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.firewallInputPath["mem"] = ctk.CTkEntry(
            master=firewallFormsFrame, state=ctk.DISABLED
        )
        self.firewallInputPath["mem"].grid(
            column=1, row=2, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.firewallInputPath["mem"].bind(
            "<1>",
            lambda event, x="mem": self.pick_file(
                entry=self.firewallInputPath[x],
                name="Firewall",
                type=x,
                isResource=True,
            ),
        )
        ctk.CTkLabel(master=firewallFormsFrame, text="Connection Count CP").grid(
            column=0, row=3, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.firewallInputPath["con-cp"] = ctk.CTkEntry(
            master=firewallFormsFrame, state=ctk.DISABLED
        )
        self.firewallInputPath["con-cp"].grid(
            column=0, row=4, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.firewallInputPath["con-cp"].bind(
            "<1>",
            lambda event, x="con-cp": self.pick_file(
                entry=self.firewallInputPath[x],
                name="Firewall",
                type=x,
                isResource=True,
            ),
        )
        ctk.CTkLabel(master=firewallFormsFrame, text="Connection Count Non-CP").grid(
            column=1, row=3, sticky="nsew", padx=5, pady=(5, 0)
        )
        self.firewallInputPath["con-noncp"] = ctk.CTkEntry(
            master=firewallFormsFrame, state=ctk.DISABLED
        )
        self.firewallInputPath["con-noncp"].grid(
            column=1, row=4, sticky="nsew", padx=5, pady=(0, 5)
        )
        self.firewallInputPath["con-noncp"].bind(
            "<1>",
            lambda event, x="con-noncp": self.pick_file(
                entry=self.firewallInputPath[x],
                name="Firewall",
                type=x,
                isResource=True,
            ),
        )

    # TODO: Add another button for options
    def __action_button(self) -> None:
        ### Action Button
        def determineConfigWindow():
            try:
                if self.configTopLevel.winfo_exists():
                    self.configTopLevel.focus()
                else:
                    raise AttributeError
            except AttributeError:
                self.configTopLevel = ConfigTopLevel(
                    master=self, controller=self.controller
                )
                self.configTopLevel.grab_set()

        actionButtonFrame = ctk.CTkFrame(master=self, fg_color="transparent")
        actionButtonFrame.pack(fill=ctk.BOTH, expand=False, padx=10, pady=10)
        ctk.CTkButton(
            master=actionButtonFrame, text="Confirm", command=self.process_data
        ).pack(side=ctk.RIGHT, ipadx=10)
        ctk.CTkButton(
            master=actionButtonFrame,
            text="Config",
            command=determineConfigWindow,
        ).pack(side=ctk.LEFT, ipadx=10)

    def pick_file(
        self,
        entry,
        name: str,
        type: str,
        isResource: bool = False,
        filePath: str = "",
    ) -> None:
        fileHandler = (
            FileHandler(initDir=self.dir).select_file(title=f"Select {name} {type}")
            if filePath == ""
            else FileHandler(initDir=self.dir, sourceFile=filePath)
        )
        sourceFile = fileHandler.sourceFile
        if sourceFile is None:
            return None
        sourceData = fileHandler.read_file(skipRows=1).sourceData
        if sourceFile != "" or not None:
            self.dir = Path(str(sourceFile).rsplit(sep="/", maxsplit=2)[0]).absolute()
            entry.configure(state=ctk.NORMAL)
            entry.delete(0, ctk.END)
            entry.insert(0, str(sourceFile))
            entry.xview_moveto(1)
            entry.configure(state=ctk.DISABLED)
            while True:
                try:
                    if not isResource:
                        self.rawData[name][type] = sourceData.assign(
                            Bandwidth=sourceData["95 Percentile"]
                            .str.extract(r"([0-9.]+)\s*\w+/s")[0]
                            .astype(float),
                            Unit=sourceData["95 Percentile"].str.extract(
                                r"[0-9.]+\s*(\w+/s)"
                            )[0],
                        ).apply(bw_unit_normalize, axis=1)
                    else:
                        self.rawData[name][type] = (
                            sourceData.rename({"Metric": "Hostname"}).drop(
                                ["Month"], axis=1
                            )
                            if "Metric" in sourceData.columns
                            else sourceData.drop(["Time"], axis=1)
                        )
                    break
                except KeyError:
                    self.rawData[name] = {}
                except Exception as Error:
                    print(Error)

    def process_data(self) -> None:
        infoError: list[str] = []
        res = {}
        for _ in self.controller.fileList[:2]:
            if _ not in self.rawData:
                infoError.append(f"{_} \t Not Fount in Input, Skipping!\n")
                continue
            res[_] = process_with_from_n_to(
                raw=(
                    self.rawData[_]
                    if "Extranet" not in self.rawData
                    else conc_df(ext=self.rawData[_], orig=self.rawData["Extranet"])
                ),
                lookUpTable=self.controller.lookUpTable[_],
            )
        for _ in self.controller.fileList[2:-1]:
            if _ not in self.rawData:
                infoError.append(f"{_} \t Not Fount in Input, Skipping!\n")
                continue
            res[_] = process_basic(
                raw=(
                    self.rawData[_]
                    if "Extranet" not in self.rawData
                    else conc_df(ext=self.rawData[_], orig=self.rawData["Extranet"])
                ),
                lookUpTable=self.controller.lookUpTable[_],
            )
        if self.controller.fileList[-2] in self.rawData.keys():
            res[self.controller.fileList[-2]] = process_f5(
                raw=self.rawData[self.controller.fileList[-2]],
                lookUpTable=self.controller.lookUpTable[self.controller.fileList[-2]],
            )
        else:
            infoError.append(
                f"{self.controller.fileList[-2]} \t Not Fount in Input, Skipping!\n"
            )
        if self.controller.fileList[-1] in self.rawData.keys():
            res[self.controller.fileList[-1]] = process_firewall(
                raw=self.rawData[self.controller.fileList[-1]],
                lookUpTable=self.controller.lookUpTable[self.controller.fileList[-1]],
            )
        else:
            infoError.append(
                f"{self.controller.fileList[-1]} \t Not Fount in Input, Skipping!\n"
            )
        if len(infoError) > 0:
            tkinter.messagebox.showwarning(
                title="Missing Value",
                message=f"{''.join(infoError)}",
            )
        extExcel = (
            ExtendedExcelProcessor()
            .save_file_loc(dirStr=self.dir)
            .ext_export(data=res)
            .open_explorer()
        )
        print(extExcel.savedFile)
        self.controller.destroy()
        return res
