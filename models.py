"""Compilation of all models for NGAGE."""

from os import getenv

import customtkinter as ctk

from helper.readconfig import AppConfig


class Environment:
    """Runtime environment configuration.

    Attributes:
        dev : bool
            True when running in development mode (ENV var DEV == "true").
        log_level : str
            Logging level, defaults to "INFO" or value from LOG_LEVEL env var.
    """

    dev: bool = False
    log_level: str = "INFO"

    def __init__(self):
        self.dev = str(getenv("DEV")).lower() == "true"
        self.log_level = getenv("LOG_LEVEL") or "INFO"


class Controller:
    """Application controller aggregating configuration and environment.

    Attributes:
        config : AppConfig
            Parsed application configuration.
        env : Environment
            Runtime environment settings.
    """

    root: ctk.CTk
    config = AppConfig()
    env = Environment()

    def __init__(self, root: ctk.CTk, config: AppConfig, env: Environment):
        self.root = root
        self.config = config
        self.env = env
