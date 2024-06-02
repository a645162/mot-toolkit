from typing import List
import os.path

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import QColor, QAction, QIcon, QDesktopServices

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout, QVBoxLayout,
    QMenuBar,
)

from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotation
)

from mot_toolkit.gui.view. \
    components.base_interface_window import BaseInterfaceWindow

from mot_toolkit.gui.view.interface.preview. \
    components.toolbox_widget import ToolboxWidget
from mot_toolkit.gui.view.interface.preview. \
    components.dataset_image_view_widget import DatasetImageView

from gui.view.interface.preview. \
    components.right_widget.label_list_widget import LabelListWidget
from gui.view.interface.preview. \
    components.right_widget.file_list_widget import FileListWidget
from gui.view.interface.preview. \
    components.right_widget.object_list_widget import ObjectListWidget


class InterFacePreview(BaseInterfaceWindow):
    annotation_directory: XAnyLabelingAnnotationDirectory = None

    current_file_list: List[XAnyLabelingAnnotation]
    current_file_str_list: List[str]

    only_file_name: bool = False

    current_annotation_object: XAnyLabelingAnnotation = None
    current_file_path: str = ""

    basic_window_title: str = "Preview Interface"

    menu: QMenuBar = None

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)

        self.current_file_list = []
        self.current_file_str_list = []

        self.annotation_directory = \
            XAnyLabelingAnnotationDirectory()
        self.annotation_directory.slot_modified.connect(
            self.__slot_annotation_directory_modified
        )

        self.menu = self.menuBar()

        self.__setup_window_properties()

        self.__init_widgets()

        self.__init_menu()

        self.__auto_load_directory()

        self.update()

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
        self.main_h_layout.addWidget(self.toolkit_widget)

        self.main_image_view = DatasetImageView(parent=self)
        self.main_image_view.slot_previous_image.connect(self.__slot_previous_image)
        self.main_image_view.slot_next_image.connect(self.__slot_next_image)
        self.main_image_view.slot_selection_changed.connect(self.__slot_selection_changed)
        self.main_h_layout.addWidget(self.main_image_view)

        self.right_widget = QWidget(parent=self)
        self.right_v_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_v_layout)

        self.r_label_list_widget = LabelListWidget(parent=self)
        self.r_label_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__label_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_label_list_widget)

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
        self.menu_settings_auto_save.setCheckable(True)
        self.menu_settings.addAction(self.menu_settings_auto_save)

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
        self.menu_help.addAction(self.menu_help_about)

        # Widget Menu

        # File List
        self.r_file_list_widget.menu_reload_file.triggered.connect(
            self.__action_file_reload
        )

        # Obj List
        self.r_object_list_widget.menu_operate_del \
            .triggered.connect(self.__action_obj_del_target)
        self.r_object_list_widget.menu_operate_del_subsequent \
            .triggered.connect(self.__action_obj_del_subsequent_target)

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
        self.r_label_list_widget.list_widget.clear()
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
            self.r_label_list_widget.list_widget.addItem(label_name)
        self.r_label_list_widget.list_widget.addItem("Disable Filter")

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
        selection_text = self.r_file_list_widget.selection_text
        index = -1
        for i, file_name in enumerate(self.annotation_directory.file_name_list):
            if file_name == selection_text:
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

    def __label_list_item_selection_changed(self):
        if self.r_label_list_widget.is_selected_last():
            self.current_file_list = \
                self.annotation_directory.annotation_file
            self.current_file_str_list = \
                self.annotation_directory.file_name_list
            return

        label_text = self.r_label_list_widget.selection_text

        self.current_file_list = \
            self.annotation_directory.label_obj_list_dict[label_text]

        self.current_file_str_list = []
        for annotation_obj in self.current_file_list:
            self.current_file_str_list.append(annotation_obj.file_name_no_extension)

        self.update_file_list_widget()

    def __file_list_item_selection_changed(self):
        if self.menu_settings_auto_save.isChecked():
            self.save_current_opened()

        self.__update_object_list_widget()

    def __slot_previous_image(self):
        selection_index = self.r_file_list_widget.selection_index
        selection_index -= 1
        if selection_index < 0:
            return
        self.r_file_list_widget.selection_index = selection_index

    def __slot_next_image(self):
        selection_index = self.r_file_list_widget.selection_index
        selection_index += 1
        if selection_index >= self.r_file_list_widget.count:
            return
        self.r_file_list_widget.selection_index = selection_index

    def __object_list_item_selection_changed(self):
        index = self.r_object_list_widget.selection_index

        self.main_image_view.set_selection_rect_index(index)

    def __slot_selection_changed(self, index):
        self.r_object_list_widget.selection_index = index

    def save_current_opened(self):
        if self.current_annotation_object is not None:
            self.current_annotation_object.save()

    def __action_window_restore_all(self):
        for annotation in self.annotation_directory.annotation_file:
            annotation.reload()

        self.__update_object_list_widget()

    def __action_window_save_all(self):
        for annotation in self.annotation_directory.annotation_file:
            annotation.save()

    def __try_to_exit(self):
        # self.save_current_opened()
        self.__action_window_save_all()

        self.close()

    def __action_file_reload(self):
        file_index = self.r_file_list_widget.selection_index

        self.annotation_directory.annotation_file[file_index].reload()

        self.__update_object_list_widget()

    def __action_obj_del_target(self):
        index = self.r_object_list_widget.selection_index

        obj = self.current_annotation_object.rect_annotation_list[index]
        self.current_annotation_object.rect_annotation_list.remove(obj)
        self.current_annotation_object.modifying()

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

        self.__update_object_list_widget()

    def check_is_have_modified(self) -> bool:
        found = False

        for annotation_obj in self.annotation_directory.annotation_file:
            if annotation_obj.is_modified:
                found = True
                print(f"{annotation_obj.file_path} is modified but not save.")

        return found
