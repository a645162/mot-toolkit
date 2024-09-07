from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class LinkLabel(QLabel):
    """
    Custom QLabel widget for displaying clickable links.
    """

    url: str

    def __init__(self, url, parent=None):
        super().__init__(parent)

        self.url = url

        # Set text interaction flags
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        # Allow automatic opening of external links
        self.setOpenExternalLinks(True)

        # Set HTML formatted link text
        self.setText(f'<a href="{url}">{url}</a>')

        # Enable word wrapping
        self.setWordWrap(True)
