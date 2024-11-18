import customtkinter as ctk


class Availability(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master)
        self.controller = controller
        self.__initUI()

    def __initUI(self):
        ctk.CTkLabel(master=self, text="Ops Metric").pack()
