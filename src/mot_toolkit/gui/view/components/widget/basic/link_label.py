from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel


class LinkLabel(QLabel):
    """
    Custom QLabel widget for displaying clickable links.
    """

    url: str
    display_text: str = ""

    def __init__(self, url, parent=None):
        super().__init__(parent)

        self.url = url

        # Set text interaction flags
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        # Allow automatic opening of external links
        # self.setOpenExternalLinks(True)

        # Set HTML formatted link text
        display_text = self.display_text if self.display_text else url
        self.setText(f'<a href="{url}">{display_text}</a>')

        # Enable word wrapping
        self.setWordWrap(True)

    @staticmethod
    def open_url(url: str):
        q_url = QUrl(url)
        QDesktopServices.openUrl(q_url)

    def mousePressEvent(self, event):
        """
        Open the link in the default web browser when the label is clicked.
        """
        self.open_url(self.url)
