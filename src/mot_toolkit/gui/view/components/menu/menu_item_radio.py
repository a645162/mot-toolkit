from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu


class MenuItemRadio(QAction):
    def __init__(self,
                 title: str,
                 parent=None,
                 action_group: QActionGroup = None,
                 menu: QMenu = None
                 ):
        super().__init__(title, parent)

        self.setCheckable(True)
        self.setChecked(False)

        if action_group is not None:
            action_group.addAction(self)

        if menu is not None:
            menu.addAction(self)
