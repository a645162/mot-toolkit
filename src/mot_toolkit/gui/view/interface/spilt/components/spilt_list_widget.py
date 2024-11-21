from typing import Optional, List

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from mot_toolkit.datatype.dataset.dataset_spilt import SpiltType
from mot_toolkit.gui.view.components.widget.list.list_with_title_widget import ListWithTitleWidget


class SpiltListWidget(ListWithTitleWidget):
    spilt_type: SpiltType

    def __init__(
            self,
            spilt_type: Optional[SpiltType] = None,
            parent=None
    ):
        super().__init__(parent=parent)

        if spilt_type is None:
            spilt_type = SpiltType.NONE
        self.spilt_type = spilt_type

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_menu()

    def __setup_widget_properties(self):
        self.set_title(self.spilt_type.to_title())

    def __init_widgets(self):
        pass

    def __init_menu(self):
        self.list_widget.have_menu = True

        q_menu: QMenu = self.list_widget.menu
        select_enable_list: List[QAction] = \
            self.list_widget.select_enable_list

        q_menu.addSeparator()

        self.menu_move_to_train = \
            QAction("Move to Train", self)
        if self.spilt_type == SpiltType.TRAIN:
            self.menu_move_to_train.setVisible(False)
        q_menu.addAction(self.menu_move_to_train)
        select_enable_list.append(self.menu_move_to_train)

        self.menu_move_to_val = \
            QAction("Move to Val", self)
        if self.spilt_type == SpiltType.VAL:
            self.menu_move_to_val.setVisible(False)
        q_menu.addAction(self.menu_move_to_val)
        select_enable_list.append(self.menu_move_to_val)

        self.menu_move_to_test = \
            QAction("Move to Test", self)
        if self.spilt_type == SpiltType.TEST:
            self.menu_move_to_test.setVisible(False)
        q_menu.addAction(self.menu_move_to_test)
        select_enable_list.append(self.menu_move_to_test)

        q_menu.addSeparator()

        self.menu_move_to_other = \
            QAction("Move to Other(Disable)", self)
        if self.spilt_type == SpiltType.NONE:
            self.menu_move_to_other.setVisible(False)
        q_menu.addAction(self.menu_move_to_other)
        select_enable_list.append(self.menu_move_to_other)

        q_menu.addSeparator()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    spilt_list_widget = SpiltListWidget()
    spilt_list_widget.show()

    app.exec()
