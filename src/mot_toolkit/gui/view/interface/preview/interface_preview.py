import json
import os.path
from typing import List

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import (
    QColor, QAction, QIcon, QDesktopServices, QActionGroup
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout, QVBoxLayout,
    QMenuBar, QInputDialog, QApplication, QMessageBox,
)

# Load Settings
from mot_toolkit.gui.common.global_settings import program_settings
from mot_toolkit.gui.view.components. \
    menu.menu_item_radio import MenuItemRadio
from mot_toolkit.gui.view.interface. \
    software.interface_about import InterFaceAbout
from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotation
)
from mot_toolkit.gui.view.components. \
    window.base_interface_window import BaseWorkInterfaceWindow
from mot_toolkit.gui.view.interface.preview. \
    components.dataset_image_view_widget import DatasetImageView
from mot_toolkit.gui.view.interface.preview. \
    components.right_widget.file_list_widget import FileListWidget
from mot_toolkit.gui.view.interface.preview. \
    components.right_widget.label_list_widget import LabelClassListWidget
from mot_toolkit.gui.view.interface.preview. \
    components.right_widget.object_list_widget import ObjectListWidget
from mot_toolkit.gui.view.interface.preview. \
    components.toolbox_widget import ToolboxWidget
from mot_toolkit.utils.logs import get_logger
from mot_toolkit.utils.system.file_explorer import show_in_explorer

logger = get_logger()


class InterFacePreview(BaseWorkInterfaceWindow):
    annotation_directory: XAnyLabelingAnnotationDirectory = None

    current_file_list: List[XAnyLabelingAnnotation]
    current_file_str_list: List[str]

    only_file_name: bool = False

    current_annotation_object: XAnyLabelingAnnotation = None
    current_file_path: str = ""

    basic_window_title: str = "Preview Interface"

    menu: QMenuBar = None

    def __init__(self, work_directory_path: str, parent=None):
        super().__init__(
            work_directory_path=work_directory_path,
            parent=parent
        )
        logger.info(f"Preview Work Directory: {work_directory_path}")

        self.current_file_list = []
        self.current_file_str_list = []

        self.annotation_directory = \
            XAnyLabelingAnnotationDirectory()
        self.annotation_directory.slot_modified.connect(
            self.__slot_annotation_directory_modified
        )

        self.menu = self.menuBar()

        self.__init_configure()

        self.__setup_window_properties()

        self.__init_widgets()

        self.__init_menu()

        self.__auto_load_directory()

        self.update()

    def __init_configure(self):
        self.jump_file_count = 1

    def __setup_window_properties(self):
        self.setWindowTitle(self.basic_window_title)

        # self.setMinimumSize(QSize(640, 320))
        self.setMinimumSize(QSize(800, 600))
        # self.setBaseSize(QSize(800, 600))

    def __init_widgets(self):
        # self.label_work_path = QLabel(parent=self)
        # self.v_layout.addWidget(self.label_work_path)

        self.main_h_widget = QWidget(parent=self)
        self.main_h_layout = QHBoxLayout()
        self.main_h_layout.setSpacing(0)
        self.main_h_widget.setLayout(self.main_h_layout)
        self.v_layout.addWidget(self.main_h_widget)

        self.toolkit_widget = ToolboxWidget(parent=self)

        self.toolkit_widget.btn_previous_frame.clicked.connect(
            self.__slot_previous_image
        )
        self.toolkit_widget.btn_next_frame.clicked.connect(
            self.__slot_next_image
        )

        self.toolkit_widget.btn_zoom_in_10.clicked.connect(
            lambda: self.main_image_view.zoom_in(1.0)
        )
        self.toolkit_widget.btn_zoom_in_5.clicked.connect(
            lambda: self.main_image_view.zoom_in(0.5)
        )
        self.toolkit_widget.btn_zoom_in.clicked.connect(
            lambda: self.main_image_view.zoom_in()
        )
        self.toolkit_widget.btn_zoom_restore.clicked.connect(
            lambda: self.main_image_view.zoom_restore()
        )
        self.toolkit_widget.btn_zoom_out.clicked.connect(
            lambda: self.main_image_view.zoom_out()
        )
        self.toolkit_widget.btn_zoom_out_5.clicked.connect(
            lambda: self.main_image_view.zoom_out(0.5)
        )
        self.toolkit_widget.btn_zoom_out_10.clicked.connect(
            lambda: self.main_image_view.zoom_out(1.0)
        )
        self.toolkit_widget.btn_zoom_fit.clicked.connect(
            lambda: self.main_image_view.set_to_fit_scale_factor()
        )
        self.toolkit_widget.btn_reverse_color.clicked.connect(
            lambda: self.main_image_view.try_to_reverse_color()
        )
        self.main_h_layout.addWidget(self.toolkit_widget)

        # Main Image View
        self.main_image_view = DatasetImageView(parent=self)

        self.main_image_view.show_box = program_settings.frame_show_box
        self.main_image_view.show_box_label = program_settings.frame_show_box_label

        self.main_image_view.slot_previous_image.connect(self.__slot_previous_image)
        self.main_image_view.slot_next_image.connect(self.__slot_next_image)
        self.main_image_view.slot_save.connect(self.save_current_opened)
        self.main_image_view.slot_selection_changed.connect(self.__slot_selection_changed)

        self.main_h_layout.addWidget(self.main_image_view)

        self.right_widget = QWidget(parent=self)
        self.right_v_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_v_layout)

        self.r_label_class_list_widget = LabelClassListWidget(parent=self)
        self.r_label_class_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__label_class_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_label_class_list_widget)

        self.r_object_list_widget = ObjectListWidget(parent=self)
        self.r_object_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__object_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_object_list_widget)

        self.r_file_list_widget = FileListWidget(parent=self)
        self.r_file_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__file_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_file_list_widget)

        self.right_v_layout.setStretch(0, 1)
        self.right_v_layout.setStretch(1, 1)
        self.right_v_layout.setStretch(2, 2)

        # self.right_widget.setFixedWidth(200)
        self.main_h_layout.addWidget(self.right_widget)

        self.main_image_view.object_menu = \
            self.r_object_list_widget.list_widget.menu

        self.main_h_layout.setStretch(0, 0)
        self.main_h_layout.setStretch(1, 8)
        self.main_h_layout.setStretch(2, 1)

    def __init_menu(self):
        # Window Menu

        # File Menu
        self.menu_file = self.menu.addMenu("File")

        self.menu_file_open_dir = \
            QAction(
                "Open Directory", self.menu_file
            )
        self.menu_file_open_dir.setIcon(
            QIcon(":/toolbox/folder_open")
        )
        self.menu_file.addAction(self.menu_file_open_dir)

        self.menu_file_refresh = \
            QAction(
                "Refresh", self.menu_file
            )
        self.menu_file_refresh.setIcon(
            QIcon(":/toolbox/folder_refresh")
        )
        self.menu_file.addAction(self.menu_file_refresh)

        self.menu_file.addSeparator()

        self.menu_file_restore_all = \
            QAction(
                "Restore All", self.menu_file
            )
        self.menu_file_restore_all.setIcon(
            QIcon(":/menu/preview/file_restore")
        )
        self.menu_file_restore_all.triggered.connect(self.__action_window_restore_all)
        self.menu_file.addAction(self.menu_file_restore_all)

        self.menu_file_save_all = \
            QAction(
                "Save All", self.menu_file
            )
        self.menu_file_save_all.setIcon(
            QIcon(":/menu/preview/file_save")
        )
        self.menu_file_save_all.triggered.connect(self.__action_window_save_all)
        self.menu_file.addAction(self.menu_file_save_all)

        self.menu_file.addSeparator()

        self.menu_file_exit = \
            QAction(
                "Exit", self.menu_file
            )
        self.menu_file_exit.setIcon(
            QIcon(":/menu/preview/file_exit")
        )
        self.menu_file_exit.triggered.connect(self.__try_to_exit)
        self.menu_file.addAction(self.menu_file_exit)

        # Edit Menu
        self.menu_edit = self.menu.addMenu("Edit")

        # File List Menu
        self.menu_file_list = self.menu.addMenu("File List")

        # Jump File Count
        self.menu_file_list_jump_file_count = \
            QAction("Jump File Count", self.menu_file_list)
        self.__set_jump_file_count(self.jump_file_count)
        self.menu_file_list_jump_file_count.triggered.connect(
            self.__action_item_jump_file_count
        )
        self.menu_file_list.addAction(self.menu_file_list_jump_file_count)

        # Frame Menu
        self.menu_frame = self.menu.addMenu("Frame")

        action_group_frame_mode = QActionGroup(self.menu_frame)

        self.action_group_frame_mode_radio_original = \
            MenuItemRadio(
                "Original Image",
                parent=action_group_frame_mode,
                action_group=action_group_frame_mode,
                menu=self.menu_frame
            )
        self.action_group_frame_mode_radio_outline = \
            MenuItemRadio(
                "Outline",
                parent=action_group_frame_mode,
                action_group=action_group_frame_mode,
                menu=self.menu_frame
            )
        self.action_group_frame_mode_radio_adjustment = \
            MenuItemRadio(
                "Contrast and Brightness Adjustment",
                parent=action_group_frame_mode,
                action_group=action_group_frame_mode,
                menu=self.menu_frame
            )

        self.action_group_frame_mode_radio_original.setChecked(True)

        self.action_group_frame_mode_radio_original.triggered.connect(self.__action_frame_mode_changed)
        self.action_group_frame_mode_radio_outline.triggered.connect(self.__action_frame_mode_changed)
        self.action_group_frame_mode_radio_adjustment.triggered.connect(self.__action_frame_mode_changed)

        self.menu_frame.addSeparator()

        # Show Box
        self.menu_frame_show_box = \
            QAction("Show Box", self.menu_frame)
        self.menu_frame_show_box.setCheckable(True)
        self.menu_frame_show_box.setChecked(program_settings.frame_show_box)
        self.menu_frame_show_box.triggered.connect(
            lambda x: self.__action_frame_show_box()
        )
        self.menu_frame.addAction(self.menu_frame_show_box)

        # Show Box Label
        self.menu_frame_show_box_label = \
            QAction("Show Box Label", self.menu_frame)
        self.menu_frame_show_box_label.setCheckable(True)
        self.menu_frame_show_box_label.setChecked(program_settings.frame_show_box_label)
        self.menu_frame_show_box_label.triggered.connect(
            lambda x: self.__action_frame_show_box_label()
        )
        self.menu_frame.addAction(self.menu_frame_show_box_label)

        # Settings Menu
        self.menu_settings = self.menu.addMenu("Settings")

        self.menu_settings_settings = \
            QAction(
                "Settings", self.menu_settings
            )
        self.menu_settings.addAction(self.menu_settings_settings)

        self.menu_settings.addSeparator()

        self.menu_settings_auto_save = \
            QAction(
                "Switching automatically to save", self.menu_settings
            )
        self.menu_settings_auto_save.setCheckable(False)
        self.menu_settings_auto_save.setChecked(program_settings.preview_auto_save)
        self.menu_settings_auto_save.triggered.connect(
            lambda: setattr(
                program_settings, "preview_auto_save",
                self.menu_settings_auto_save.isChecked()
            )
        )
        self.menu_settings.addAction(self.menu_settings_auto_save)

        self.menu_settings_auto_select_same_tag = \
            QAction(
                "Switching automatically select same tag", self.menu_settings
            )
        self.menu_settings_auto_select_same_tag.setCheckable(True)
        self.menu_settings_auto_select_same_tag.setChecked(program_settings.preview_auto_select_same_tag)
        self.menu_settings_auto_select_same_tag.triggered.connect(
            lambda: setattr(
                program_settings, "preview_auto_select_same_tag",
                self.menu_settings_auto_select_same_tag.isChecked()
            )
        )
        self.menu_settings.addAction(self.menu_settings_auto_select_same_tag)

        # Help Menu
        self.menu_help = self.menu.addMenu("Help")

        self.menu_help_website = \
            QAction(
                "Open Website", self.menu_help
            )
        self.menu_help_website.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl(
                r"https://github.com/a645162/mot-toolkit"
            ))
        )
        self.menu_help.addAction(self.menu_help_website)

        self.menu_help_about = \
            QAction(
                "About", self.menu_help
            )
        self.menu_help_about.triggered.connect(
            lambda x: InterFaceAbout(parent=self).show()
        )
        self.menu_help.addAction(self.menu_help_about)

        # Widget Menu

        # File List
        self.r_file_list_widget.menu_reload_file.triggered.connect(
            self.__action_file_reload
        )
        self.r_file_list_widget.menu_copy_path_image.triggered.connect(
            self.__action_file_list_copy_path_image
        )
        self.r_file_list_widget.menu_copy_path_json.triggered.connect(
            self.__action_file_list_copy_path_json
        )
        self.r_file_list_widget.menu_show_in_explorer.triggered.connect(
            self.__action_file_list_show_in_explorer
        )

        # Obj List
        self.r_object_list_widget.menu_operate_del \
            .triggered.connect(self.__action_obj_del_target)
        self.r_object_list_widget.menu_operate_del_subsequent \
            .triggered.connect(self.__action_obj_del_subsequent_target)

        self.r_object_list_widget.menu_unselect_all \
            .triggered.connect(self.__action_obj_unselect_all)

    def update(self):
        super().update()

        self.setWindowTitle(
            self.basic_window_title + " - " + self.work_directory_path
        )
        # self.label_work_path.setText(
        #     "Work Directory: " + self.work_directory_path
        # )

    def load_directory(self):
        # Clear
        self.current_file_str_list.clear()
        self.r_label_class_list_widget.list_widget.clear()
        self.r_object_list_widget.list_widget.clear()
        self.r_file_list_widget.list_widget.clear()

        self.annotation_directory.dir_path = self.work_directory_path
        self.annotation_directory.walk_dir()
        self.annotation_directory.sort_path(group_directory=True)
        self.annotation_directory.load_json_files()
        self.annotation_directory.update_label_list()

        self.only_file_name = self.annotation_directory.can_only_file_name

        # Update Label List
        for label_name in self.annotation_directory.label_list:
            self.r_label_class_list_widget.list_widget.addItem(label_name)
        self.r_label_class_list_widget.list_widget.addItem("Disable Filter")
        self.r_label_class_list_widget.update()

        # Update File List
        self.current_file_list = \
            self.annotation_directory.annotation_file
        self.current_file_str_list = \
            self.annotation_directory.file_name_list

        self.update_file_list_widget()

        if self.r_file_list_widget.count > 0:
            self.r_file_list_widget.selection_index = 0

    def __slot_annotation_directory_modified(self):
        self.update_file_list_widget()

    def update_file_list_widget(self):
        annotation_obj_list: List[XAnyLabelingAnnotation] = \
            self.current_file_list

        if len(annotation_obj_list) != self.r_file_list_widget.count:
            # Clear
            self.r_file_list_widget.list_widget.clear()

            for i, current_annotation_obj in enumerate(annotation_obj_list):
                self.r_file_list_widget.list_widget.addItem(
                    self.current_file_str_list[i]
                )

        for i, current_annotation_obj in enumerate(annotation_obj_list):
            current_item = self.r_file_list_widget.list_widget.item(i)

            base_text = self.current_file_str_list[i]
            if current_annotation_obj.is_modified:
                current_item.setForeground(QColor(255, 0, 0))
                base_text = f"* {base_text}"
            else:
                current_item.setForeground(QColor(0, 0, 0))

            current_item.setText(base_text)

        self.r_file_list_widget.update()

    def __auto_load_directory(self):
        if not os.path.isdir(self.work_directory_path):
            return

        self.load_directory()

    def __update_object_list_widget(self):
        # Save Current Selected Label
        obj_selection_index = self.r_object_list_widget.selection_index
        current_label_text = ""
        if 0 <= obj_selection_index < len(self.current_annotation_object.rect_annotation_list):
            current_label_text = \
                self.current_annotation_object \
                    .rect_annotation_list[obj_selection_index] \
                    .label

        file_selection_text = self.r_file_list_widget.selection_text
        if file_selection_text.startswith("* "):
            file_selection_text = file_selection_text[2:]
        index = -1
        for i, file_name in enumerate(self.annotation_directory.file_name_list):
            if file_name == file_selection_text:
                index = i
                break
        if index == -1:
            return

        self.current_annotation_object = \
            self.annotation_directory.annotation_file[index]
        self.current_file_path = self.current_annotation_object.file_path

        self.main_image_view.update_dataset_annotation_path(
            self.current_annotation_object
        )

        self.r_object_list_widget.list_widget.clear()
        for rect_item in self.current_annotation_object.rect_annotation_list:
            self.r_object_list_widget.list_widget.addItem(
                f"{rect_item.label}({rect_item.group_id})"
            )
        self.r_object_list_widget.update()

        # Auto Select
        if self.is_in_class_filter_mode():
            self.__update_label_class_auto_select()
        else:
            if program_settings.preview_auto_select_same_tag:
                self.select_target_tag(current_label_text)

    def is_in_class_filter_mode(self) -> bool:
        return (
                self.r_label_class_list_widget.count > 1 and
                self.r_label_class_list_widget.selection_index != -1 and
                self.r_label_class_list_widget.selection_index != self.r_label_class_list_widget.count - 1
        )

    def __update_label_class_auto_select(self):
        if self.is_in_class_filter_mode():
            # Have Selected Label Class
            label_name = self.r_label_class_list_widget.selection_text
            self.select_target_tag(label_name)

    def select_target_tag(self, tag_text: str) -> bool:
        if len(tag_text.strip()) == 0:
            return False

        target_label_index = -1
        for i, rect_item in enumerate(self.current_annotation_object.rect_annotation_list):
            if rect_item.label == tag_text:
                target_label_index = i
                break

        # Not Found
        if target_label_index == -1:
            return False

        self.r_object_list_widget.selection_index = target_label_index

        return True

    def __label_class_list_item_selection_changed(self):
        if (
                self.r_label_class_list_widget.count == 1 or
                self.r_label_class_list_widget.is_selected_last()
        ):
            self.current_file_list = \
                self.annotation_directory.annotation_file
            self.current_file_str_list = \
                self.annotation_directory.file_name_list
        else:
            label_text = self.r_label_class_list_widget.selection_text

            self.current_file_list = \
                self.annotation_directory.label_obj_list_dict[label_text]

            self.current_file_str_list = []
            for annotation_obj in self.current_file_list:
                self.current_file_str_list.append(annotation_obj.file_name_no_extension)

        self.update_file_list_widget()

        self.__update_label_class_auto_select()

    def __file_list_item_selection_changed(self):
        if self.menu_settings_auto_save.isChecked():
            self.save_current_opened()

        self.__update_object_list_widget()

    def __slot_previous_image(self):
        self.next_previous_image(is_next=False)

    def __slot_next_image(self):
        self.next_previous_image(is_next=True)

    def next_previous_image(self, is_next: bool = True):
        selection_index = self.r_file_list_widget.selection_index
        file_count = self.r_file_list_widget.count
        jump_file_count = self.jump_file_count

        if is_next:
            selection_index += jump_file_count
        else:
            selection_index -= jump_file_count

        while selection_index >= file_count:
            selection_index -= 1

        while selection_index < 0:
            selection_index += 1

        self.r_file_list_widget.selection_index = selection_index

    def __object_list_item_selection_changed(self):
        index = self.r_object_list_widget.selection_index

        self.main_image_view.set_selection_rect_index(index)

    def __slot_selection_changed(self, index):
        self.r_object_list_widget.selection_index = index

    def save_current_opened(self):
        if self.current_annotation_object is not None:
            if self.current_annotation_object.save():
                self.__successful_saved(self.current_annotation_object)

    def __action_window_restore_all(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to restore all?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for annotation in self.annotation_directory.annotation_file:
                annotation.reload()

            self.__update_object_list_widget()

    def __action_window_save_all(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to save all?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for annotation in self.annotation_directory.annotation_file:
                if annotation.save():
                    self.__successful_saved(annotation)

    def __try_to_exit(self):
        # self.save_current_opened()
        if self.check_is_have_modified():
            self.__action_window_save_all()

        self.close()

    def __action_file_reload(self):
        file_index = self.r_file_list_widget.selection_index

        self.annotation_directory.annotation_file[file_index].reload()

        self.__update_object_list_widget()

    def __get_selection_image_path(self):
        file_index = self.r_file_list_widget.selection_index

        file_path = self.annotation_directory.annotation_file[file_index].pic_path

        return file_path

    def __get_selection_json_path(self):
        file_index = self.r_file_list_widget.selection_index

        return self.annotation_directory.annotation_file[file_index].file_path

    def __action_file_list_copy_path_image(self):
        file_path = self.__get_selection_image_path()

        # Copy Path
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)

    def __action_file_list_copy_path_json(self):
        file_path = self.__get_selection_json_path()

        # Copy Path
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)

    def __action_file_list_show_in_explorer(self):
        file_path = self.__get_selection_image_path()

        show_in_explorer(file_path)

    def __action_obj_del_target(self):
        index = self.r_object_list_widget.selection_index

        rect_annotation_list = self.current_annotation_object.rect_annotation_list
        obj = rect_annotation_list[index]
        rect_annotation_list.remove(obj)

        self.current_annotation_object.modifying()

        self.r_object_list_widget.selection_index = -1

        self.__update_object_list_widget()

    def __action_obj_del_subsequent_target(self):
        file_index = self.r_file_list_widget.selection_index

        index = self.r_object_list_widget.selection_index
        print(f"[{index}]Delete the target in subsequent frames")
        label = self.current_annotation_object.rect_annotation_list[index].label
        print(f"Delete Label:{label}")

        # self.current_annotation_object.del_by_label(label)
        for i, annotation_obj in enumerate(self.annotation_directory.annotation_file):
            if i < file_index:
                continue

            annotation_obj.del_by_label(label)

        self.r_object_list_widget.selection_index = -1

        self.__update_object_list_widget()

    def __action_obj_unselect_all(self):
        self.r_object_list_widget.selection_index = -1

    def __action_frame_mode_changed(self):
        if self.action_group_frame_mode_radio_original.isChecked():
            self.__action_frame_mode(0)
        elif self.action_group_frame_mode_radio_outline.isChecked():
            self.__action_frame_mode(1)
        elif self.action_group_frame_mode_radio_adjustment.isChecked():
            self.__action_frame_mode(2)
        else:
            self.__action_frame_mode(0)

    def __action_frame_mode(self, mode: int):
        match mode:
            case 0:
                # Original Image
                print("Original Image")
            case 1:
                # Outline Image
                print("Outline Image")
            case 2:
                # Adjustment Image
                print("Adjust Image Contrast and Brightness")
            case _:
                print("Unknown mode")

    def __action_frame_show_box(self):
        value = self.menu_frame_show_box.isChecked()

        self.main_image_view.show_box = value

        setattr(
            program_settings, "frame_show_box",
            value
        )

    def __action_frame_show_box_label(self):
        value = self.menu_frame_show_box_label.isChecked()

        self.main_image_view.show_box_label = value

        setattr(
            program_settings, "frame_show_box_label",
            value
        )

    def check_is_have_modified(self) -> bool:
        found = False

        for annotation_obj in self.annotation_directory.annotation_file:
            if annotation_obj.is_modified:
                found = True
                print(f"{annotation_obj.file_path} is modified but not save.")

        return found

    def __action_item_jump_file_count(self):
        number, ok = QInputDialog.getInt(
            self,
            "Input Dialog",
            "Enter a number for Jump File Count:",
            value=self.jump_file_count
        )
        if ok:
            self.__set_jump_file_count(number)

    def __set_jump_file_count(self, jump_file_count: int = 1):
        self.jump_file_count = jump_file_count
        self.menu_file_list_jump_file_count.setText(f"Jump File Count: {self.jump_file_count}")

    def __successful_saved(self, annotation_obj: XAnyLabelingAnnotation):
        # print("Save Successful!")

        record_path = self.annotation_directory.save_record_path
        # print(record_path)

        modify_record_dict: dict
        with open(record_path, "r", encoding="utf-8") as f:
            record_text = f.read().strip()
            if len(record_text):
                modify_record_dict = json.loads(record_text)
            else:
                modify_record_dict = {}

        if annotation_obj.file_name not in modify_record_dict.keys():
            modify_record_dict[annotation_obj.file_name] = {}

        json_str = json.dumps(modify_record_dict, indent=4)
        # print("json_str\n", json_str)

        with open(record_path, "w", encoding="utf-8") as f:
            f.write(json_str)

    def closeEvent(self, event):
        super().closeEvent(event)

        if not self.check_is_have_modified():
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "File not save",
            "You have not saved some files.\n"
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
