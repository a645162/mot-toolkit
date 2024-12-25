from typing import List

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from mot_toolkit.gui.view.components.widget. \
    list.list_with_title_widget import ListWithTitleWidget
from mot_toolkit.gui.view.interface.preview.components.dialog.padding_input_dialog import PaddingInputDialog
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class ObjectListWidget(ListWithTitleWidget):
    padding_top: float = 0
    padding_bottom: float = 0
    padding_left: float = 0
    padding_right: float = 0

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_menu()

    def __setup_widget_properties(self):
        self.set_title("Annotation Object")

    def __init_widgets(self):
        pass

    def __init_menu(self):
        self.list_widget.have_menu = True

        q_menu: QMenu = self.list_widget.menu
        select_enable_list: List[QAction] = \
            self.list_widget.select_enable_list

        q_menu.addSeparator()

        self.menu_subsequent_new_id = \
            QAction(
                "Assign a new ID in subsequent frames",
                q_menu
            )
        q_menu.addAction(self.menu_subsequent_new_id)
        select_enable_list.append(self.menu_subsequent_new_id)

        q_menu.addSeparator()

        self.menu_change_class = \
            QAction(
                "Change Class",
                q_menu
            )
        q_menu.addAction(self.menu_change_class)
        select_enable_list.append(self.menu_change_class)

        q_menu.addSeparator()

        self.menu_copy_subsequent = \
            QAction(
                "Copy the target in subsequent frames(Label)",
                q_menu
            )
        q_menu.addAction(self.menu_copy_subsequent)
        select_enable_list.append(self.menu_copy_subsequent)

        self.menu_copy_between = \
            QAction(
                "Copy the target between frames(Label)",
                q_menu
            )
        q_menu.addAction(self.menu_copy_between)
        select_enable_list.append(self.menu_copy_between)

        self.menu_linear_interpolation = \
            QAction(
                "Linear Interpolation",
                q_menu
            )
        q_menu.addAction(self.menu_linear_interpolation)
        select_enable_list.append(self.menu_linear_interpolation)

        self.menu_linear_interpolation_previous = \
            QAction(
                "Linear Interpolation (Previous)",
                q_menu
            )
        q_menu.addAction(self.menu_linear_interpolation_previous)
        select_enable_list.append(self.menu_linear_interpolation_previous)

        q_menu.addSeparator()

        self.menu_operate_del = \
            QAction(
                "Delete the target",
                q_menu
            )
        q_menu.addAction(self.menu_operate_del)
        select_enable_list.append(self.menu_operate_del)

        self.menu_operate_del_subsequent = \
            QAction(
                "Delete the target in subsequent frames(Label)",
                q_menu
            )
        q_menu.addAction(self.menu_operate_del_subsequent)
        select_enable_list.append(self.menu_operate_del_subsequent)

        self.menu_operate_del_between = \
            QAction(
                "Delete the target between frames(Label)",
                q_menu
            )
        q_menu.addAction(self.menu_operate_del_between)
        select_enable_list.append(self.menu_operate_del_between)

        q_menu.addSeparator()

        self.menu_mark_appear = \
            QAction(
                "Mark as Appear Frame",
                q_menu
            )
        q_menu.addAction(self.menu_mark_appear)
        select_enable_list.append(self.menu_mark_appear)

        q_menu.addSeparator()

        self.menu_copy_position_float = \
            QAction(
                "Copy Position to Clipboard[float]",
                q_menu
            )
        q_menu.addAction(self.menu_copy_position_float)
        select_enable_list.append(self.menu_copy_position_float)

        self.menu_object_info = \
            QAction(
                "Object Info",
                q_menu
            )
        q_menu.addAction(self.menu_object_info)
        select_enable_list.append(self.menu_object_info)

        q_menu.addSeparator()

        self.menu_dl_sam2 = \
            QAction(
                "DL: SAM2",
                q_menu
            )
        q_menu.addAction(self.menu_dl_sam2)
        select_enable_list.append(self.menu_dl_sam2)

        self.menu_dl_near_mode = \
            QAction(
                "   Near Mode",
                q_menu
            )
        self.menu_dl_near_mode.setCheckable(True)
        self.menu_dl_near_mode.setChecked(False)
        # self.menu_dl_sam2.triggered.connect(
        #     lambda: self.menu_dl_near_mode.setChecked(self.menu_dl_sam2.isChecked())
        # )
        q_menu.addAction(self.menu_dl_near_mode)

        self.menu_dl_export_task = \
            QAction(
                "DL: Export Task",
                q_menu
            )
        q_menu.addAction(self.menu_dl_export_task)
        select_enable_list.append(self.menu_dl_export_task)

        q_menu.addSeparator()

        self.menu_dl_sam2_subsequence = \
            QAction(
                "DL: SAM2 Subsequence",
                q_menu
            )
        q_menu.addAction(self.menu_dl_sam2_subsequence)
        select_enable_list.append(self.menu_dl_sam2_subsequence)

        self.menu_dl_sam2_subsequence_opt_copy = \
            QAction(
                "   Copy Previous",
                q_menu
            )
        self.menu_dl_sam2_subsequence_opt_copy.setCheckable(True)
        self.menu_dl_sam2_subsequence_opt_copy.setChecked(False)
        q_menu.addAction(self.menu_dl_sam2_subsequence_opt_copy)

        self.menu_dl_sam2_subsequence_opt_enable_padding = \
            QAction(
                "   Enable Padding",
                q_menu
            )
        self.menu_dl_sam2_subsequence_opt_enable_padding.setCheckable(True)
        self.menu_dl_sam2_subsequence_opt_enable_padding.setChecked(False)
        q_menu.addAction(self.menu_dl_sam2_subsequence_opt_enable_padding)

        self.menu_dl_sam2_subsequence_opt_padding_info = \
            QAction(
                "   Padding Info",
                q_menu
            )
        self.menu_dl_sam2_subsequence_opt_padding_info.triggered.connect(
            self.__action_padding_settings
        )
        q_menu.addAction(self.menu_dl_sam2_subsequence_opt_padding_info)
        self.__update_padding_info()

        q_menu.addSeparator()

        self.menu_unselect_all = \
            QAction(
                "Unselect All",
                q_menu
            )
        q_menu.addAction(self.menu_unselect_all)
        select_enable_list.append(self.menu_unselect_all)

    def __update_padding_info(self):
        self.menu_dl_sam2_subsequence_opt_padding_info.setText(
            f"   Top({self.padding_top}), "
            f"Bottom({self.padding_bottom}), "
            f"Left({self.padding_left}), "
            f"Right({self.padding_right})"
        )

    def __action_padding_settings(self):
        padding_input_dialog = PaddingInputDialog(
            default_values=(
                self.padding_top,
                self.padding_bottom,
                self.padding_left,
                self.padding_right
            ),
            parent=self
        )
        if padding_input_dialog.exec_() != PaddingInputDialog.DialogCode.Accepted:
            return

        padding_value_tuple = padding_input_dialog.get_padding_values()
        if padding_value_tuple is None:
            logger.error("Invalid padding value")
            return

        (
            self.padding_top,
            self.padding_bottom,
            self.padding_left,
            self.padding_right
        ) = padding_value_tuple

        self.__update_padding_info()
