"""Data models shared across the NGAGE application.

Define the ``Environment`` and ``Controller`` classes that encapsulate
runtime environment settings and wire together the application's root
window, configuration, and environment into a single dependency
container passed to every view.
"""

from os import getenv

import customtkinter as ctk

from helper.readconfig import AppConfig


class Environment:
    """Runtime environment configuration read from OS environment variables.

    Inspect the ``DEV`` and ``LOG_LEVEL`` environment variables at
    construction time and expose them as typed attributes for use
    throughout the application.

    Attributes:
        dev (bool): ``True`` when the ``DEV`` environment variable is
            set to ``"true"`` (case-insensitive), enabling development
            mode features such as config reset.
        log_level (str): Logging verbosity level. Defaults to ``"INFO"``
            unless overridden by the ``LOG_LEVEL`` environment variable.
    """

    dev: bool = False
    log_level: str = "INFO"

    def __init__(self):
        self.dev = str(getenv("DEV")).lower() == "true"
        self.log_level = getenv("LOG_LEVEL") or "INFO"


class Controller:
    """Central dependency container shared with all views.

    Aggregate the root ``CTk`` window, the parsed ``AppConfig``, and the
    ``Environment`` into a single object that is passed to every view
    frame, giving each view access to application-wide state without
    global variables.

    Attributes:
        root (ctk.CTk): The root CustomTkinter application window.
        config (AppConfig): Parsed application configuration loaded from
            the temporary config file.
        env (Environment): Runtime environment settings read from OS
            environment variables.
    """

    root: ctk.CTk
    config = AppConfig()
    env = Environment()

    def __init__(self, root: ctk.CTk, config: AppConfig, env: Environment):
        self.root = root
        self.config = config
        self.env = env
