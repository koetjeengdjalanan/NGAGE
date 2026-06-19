"""Entry Point for the Application, initializes the main window and handles global errors."""

import sys
import traceback
from pathlib import Path

import customtkinter as ctk
import toml

from helper.getfile import GetFile
from helper.readconfig import AppConfig
from view.availability import Availability
from view.capacity import Capacity


class App(ctk.CTk):
    """Main application window for DBS Grafana Reporting Automation.

    Initializes the main Tkinter window with tabs for Capacity and Availability views.

    Attributes:
        env (dict): Environment configuration dictionary.
        config (AppConfig): Application configuration object.
    """

    def __init__(self, start_size: tuple[int, int], env: dict = {"DEV": False}):
        """Initialize the main application window.

        Args:
            start_size (tuple[int, int]): Initial window size (width, height).
            env (dict, optional): Environment configuration dictionary. Defaults to {"DEV": False}.
        """
        super().__init__()
        GetFile.setIcon(self)
        self.title("DBS | Grafana Reporting Automation")
        self.geometry(
            f"{start_size[0]}x{start_size[1]}+{(self.winfo_screenwidth() - start_size[0]) // 4}"
            f"+{(self.winfo_screenheight() - start_size[1]) // 4}"
        )
        self.resizable(False, False)
        self.env = env
        self.config: AppConfig = AppConfig(reset=self.env.get("DEV", False))
        tabView = ctk.CTkTabview(master=self)
        tabView.pack(fill="both", expand=True)
        tabView.add(name="Capacity")
        Capacity(master=tabView.tab(name="Capacity"), controller=self).pack(fill="both", expand=True)
        tabView.add(name="Availability")
        Availability(master=tabView.tab(name="Availability"), controller=self).pack(fill="both", expand=True)


# IDEA: Add a function to writ a default env file if not exist to tempdir and use it as default
# value and make it editable!
def environment() -> dict:
    """Load environment variables from a .env.toml file if it exists, otherwise return default values."""
    envPath = Path("./.env.toml").absolute()
    if envPath.is_file():
        with open(envPath, "r") as file:
            return toml.load(file)
    return {
        "DEV": False,
    }


def handle_error(exception, value, tb):
    """Global error handler that displays an error message in a custom Tkinter window."""
    print(exception, value, tb)
    error_window = ctk.CTkToplevel(takefocus=True)
    error_window.title("An error has occurred")
    error_window.attributes("-topmost", True)
    error_window.bell()

    # Disable the main app window
    if sys.platform.startswith("win"):
        app.attributes("-disabled", True)

    def on_close():
        if sys.platform.startswith("win"):
            app.attributes("-disabled", False)
        error_window.destroy()
        app.destroy()

    def on_focus(event):
        error_window.bell()
        error_window.focus()

    error_window.bind("<FocusOut>", on_focus)

    ctk.CTkLabel(master=error_window, text=value, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 0), padx=20)
    error_message = ctk.CTkTextbox(master=error_window, wrap="none")
    error_message.insert(index="0.0", text=traceback.format_exc(chain=True), tags="error")
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
