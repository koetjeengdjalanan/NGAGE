"""Application entry point for the DBS Grafana Reporting Automation tool.

Initializes the main CustomTkinter window with tabbed views for Capacity
and Availability analysis. Provides a global error handler that captures
unhandled exceptions and displays them in a modal error window, preventing
silent crashes during user interaction.
"""

import sys
import traceback
from pathlib import Path

import customtkinter as ctk
import toml

from helper.getfile import GetFile
from helper.readconfig import AppConfig
from models import Controller, Environment
from view.availability import Availability
from view.capacity import Capacity


class App(ctk.CTk):
    """Main application window for DBS Grafana Reporting Automation.

    Create the root CustomTkinter window and populate it with a tabbed
    interface containing Capacity and Availability analysis views. The
    window is positioned at one-quarter offset from the top-left corner
    of the screen and is not resizable.
    """

    def __init__(self, start_size: tuple[int, int], env: dict = {"DEV": False}):
        """Initialize the main application window with tabbed views.

        Set the window icon, title, geometry, and create a ``CTkTabview``
        containing the Capacity and Availability tabs. An ``AppConfig``
        and ``Environment`` are instantiated and bundled into a
        ``Controller`` that is shared with every child view.

        Args:
            start_size (tuple[int, int]): Initial window dimensions as
                ``(width, height)`` in pixels.
            env (dict, optional): Environment configuration dictionary.
                Defaults to ``{"DEV": False}``.
        """
        super().__init__()
        GetFile.setIcon(self)
        self.title("DBS | Grafana Reporting Automation")
        self.geometry(
            f"{start_size[0]}x{start_size[1]}+{(self.winfo_screenwidth() - start_size[0]) // 4}"
            f"+{(self.winfo_screenheight() - start_size[1]) // 4}"
        )
        self.resizable(False, False)
        env_var = Environment()
        controller = Controller(root=self, config=AppConfig(reset=env_var.dev), env=env_var)
        tabView = ctk.CTkTabview(master=self)
        tabView.pack(fill="both", expand=True)
        tabView.add(name="Capacity")
        Capacity(master=tabView.tab(name="Capacity"), controller=controller).pack(fill="both", expand=True)
        tabView.add(name="Availability")
        Availability(master=tabView.tab(name="Availability"), controller=controller).pack(fill="both", expand=True)


# IDEA: Add a function to writ a default env file if not exist to tempdir and use it as default
# value and make it editable!
def environment() -> dict:
    """Load environment configuration from a local ``.env.toml`` file.

    Search for a ``.env.toml`` file in the current working directory. If
    the file exists, parse it with the ``toml`` library and return the
    resulting dictionary. Otherwise, return a default configuration with
    ``DEV`` set to ``False``.

    Returns:
        dict: A dictionary of environment key-value pairs. At minimum
            contains the ``DEV`` key.
    """
    envPath = Path("./.env.toml").absolute()
    if envPath.is_file():
        with open(envPath, "r") as file:
            return toml.load(file)
    return {
        "DEV": False,
    }


def handle_error(exception, value, tb):
    """Display an unhandled exception in a modal error window.

    Create a ``CTkToplevel`` window that shows the exception value as a
    heading and the full traceback in a read-only text box. The main
    application window is disabled (on Windows) while the error window
    is visible, and closing the error window also destroys the
    application.

    Args:
        exception (type): The exception class.
        value (BaseException): The exception instance.
        tb (types.TracebackType): The traceback object.
    """
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
