"""Module for retrieving asset file paths."""

import os
import sys


class GetFile:
    """Helper class to resolve paths for application assets."""

    @staticmethod
    def getAssets(file_name: str) -> str:
        """Get the absolute path to an asset file.

        Args:
            file_name (str): The name of the asset file.

        Returns:
            str: The absolute path to the asset file.

        Raises:
            FileNotFoundError: If the asset file does not exist.
        """
        if hasattr(sys, "_MEIPASS"):
            path = os.path.join(sys._MEIPASS, "assets", file_name)
        else:
            path = os.path.join(os.path.dirname(__file__), "..", "assets", file_name)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"The asset file '{file_name}' does not exist at path '{path}'"
            )

        return path

    @staticmethod
    def setIcon(window) -> None:
        """Set the window icon, handling cross-platform differences.

        Args:
            window: The Tkinter or CustomTkinter window instance.
        """
        try:
            icon_path = GetFile.getAssets(file_name="favicon.ico")
            if sys.platform.startswith("win"):
                window.iconbitmap(icon_path)
            else:
                from PIL import Image, ImageTk
                window._icon = ImageTk.PhotoImage(Image.open(icon_path))
                window.iconphoto(True, window._icon)
        except Exception:
            pass

