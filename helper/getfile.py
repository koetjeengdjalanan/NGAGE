"""Resolve paths to bundled application assets.

Provide the ``GetFile`` helper class with static methods for locating
asset files at runtime, supporting both normal development execution
and PyInstaller-bundled single-file executables where assets are
extracted to a temporary ``_MEIPASS`` directory.
"""

import os
import sys


class GetFile:
    """Static utility class for resolving and applying application assets.

    All methods are ``@staticmethod`` — no instance state is needed.
    The class serves as a namespace grouping asset-related helpers.
    """

    @staticmethod
    def getAssets(file_name: str) -> str:
        """Return the absolute path to a named asset file.

        When running inside a PyInstaller bundle, look for the asset
        under ``sys._MEIPASS/assets/``. Otherwise, resolve relative to
        this module's parent ``assets/`` directory. Raise an error if
        the resolved path does not exist on disk.

        Args:
            file_name (str): The file name (including extension) of the
                asset to locate, e.g. ``"favicon.ico"``.

        Returns:
            str: The absolute filesystem path to the asset file.

        Raises:
            FileNotFoundError: If the asset file cannot be found at the
                resolved path.
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
        """Apply the application icon to a Tkinter or CustomTkinter window.

        On Windows, use ``iconbitmap`` with the ``.ico`` file. On Linux
        and macOS, load the icon via Pillow and call ``iconphoto``.
        Silently ignore any errors (e.g. missing icon file) so the
        application can still launch without an icon.

        Args:
            window: The ``Tk`` or ``CTk`` window instance to which the
                icon will be applied.
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

