from pathlib import Path
import traceback
import customtkinter as ctk
import toml

from helper.getfile import GetFile
from helper.readconfig import AppConfig
from view.availability import Availability
from view.capacity import Capacity


class App(ctk.CTk):
    def __init__(self, start_size: tuple[int], env: dict = {"DEV": False}):
        super().__init__()
        self.iconbitmap(GetFile.getAssets(file_name="favicon.ico"))
        self.title("DBS | Grafana Reporting Automation")
        self.geometry(
            f"{start_size[0]}x{start_size[1]}+{(self.winfo_screenwidth() - start_size[0]) // 4}+{(self.winfo_screenheight() - start_size[1]) // 4}"
        )
        self.resizable(False, False)
        self.env = env
        self.config = AppConfig()
        tabView = ctk.CTkTabview(master=self)
        tabView.pack(fill="both", expand=True)
        tabView.add(name="Capacity")
        Capacity(master=tabView.tab(name="Capacity"), controller=self).pack(
            fill="both", expand=True
        )
        tabView.add(name="Availability")
        Availability(master=tabView.tab(name="Availability"), controller=self).pack(
            fill="both", expand=True
        )


# IDEA: Add a function to writ a default env file if not exist to tempdir and use it as default value and make it editable!
def environment() -> dict:
    envPath = Path("./.env.toml").absolute()
    if envPath.is_file():
        with open(envPath, "r") as file:
            return toml.load(file)
    return {
        "DEV": False,
    }


def handle_error(exception, value, tb):
    print(exception, value, tb)
    error_window = ctk.CTkToplevel(takefocus=True)
    error_window.title("An error has occurred")
    error_window.attributes("-topmost", True)
    error_window.bell()

    # Disable the main app window
    app.attributes("-disabled", True)

    def on_close():
        app.attributes("-disabled", False)
        error_window.destroy()
        app.destroy()

    def on_focus(event):
        error_window.bell()
        error_window.focus()

    error_window.bind("<FocusOut>", on_focus)

    ctk.CTkLabel(
        master=error_window, text=value, font=ctk.CTkFont(size=24, weight="bold")
    ).pack(pady=(20, 0), padx=20)
    error_message = ctk.CTkTextbox(master=error_window, wrap="none")
    error_message.insert(
        index="0.0", text=traceback.format_exc(chain=True), tags="error"
    )
    error_message.configure(state="disabled")
    error_message.pack(pady=20, padx=20, fill="both", expand=True)
    error_button = ctk.CTkButton(
        master=error_window,
        text="Close",
        command=on_close,
    )
    error_button.pack(pady=10, padx=20, side="right")


if __name__ == "__main__":
    import sys

    sys.excepthook = handle_error
    app = App(start_size=(600, 700), env=environment())
    app.report_callback_exception = handle_error
    app.mainloop()
