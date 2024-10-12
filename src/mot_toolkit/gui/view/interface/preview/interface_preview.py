import json
import os.path
from typing import List

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import (
    QColor, QAction, QIcon, QDesktopServices, QActionGroup, Qt
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout, QVBoxLayout,
    QMenuBar,
    QDialog, QInputDialog, QMessageBox,
)

# Load Settings
from mot_toolkit.gui.common.global_settings import program_settings
from mot_toolkit.gui.view.components. \
    dialog.dialog_input_2_int import DialogInput2Int
from mot_toolkit.gui.view.components. \
    menu.menu_item_radio import MenuItemRadio
from mot_toolkit.gui.view.components.widget. \
    basic.base_image_view_graphics import ImageDisplayType
from mot_toolkit.gui.view.components. \
    widget.rect.image_rect import ImageRect
from mot_toolkit.gui.view.interface. \
    preview.components.detail.detail_widget import DetailWidget
from mot_toolkit.gui.view.interface.preview.components. \
    option.dialog_brightness_contrast import DialogBrightnessContrast
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

        self.main_image_view.only_show_selected = program_settings.menu_rect_only_show_selected
        self.main_image_view.show_box = program_settings.menu_rect_show_box
        self.main_image_view.show_box_label = program_settings.menu_rect_show_box_label

        self.main_image_view.slot_previous_image.connect(self.__slot_previous_image)
        self.main_image_view.slot_next_image.connect(self.__slot_next_image)
        self.main_image_view.slot_save.connect(self.save_current_opened)
        self.main_image_view.slot_selection_changed.connect(self.__slot_selection_changed)
        self.main_image_view.slot_property_changed.connect(self.__slot_property_changed)

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
        self.r_file_list_widget.show_current_index = True
        self.r_file_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__file_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_file_list_widget)

        self.r_file_detail_widget_container = QWidget(parent=self)
        self.r_file_detail_widget_container_layout = QVBoxLayout()
        self.r_file_detail_widget_container.setLayout(
            self.r_file_detail_widget_container_layout
        )
        self.right_v_layout.addWidget(self.r_file_detail_widget_container)

        self.r_file_detail_widget = DetailWidget(parent=self)
        self.r_file_detail_widget_container_layout.addWidget(
            self.r_file_detail_widget
        )

        self.right_v_layout.setStretch(0, 1)
        self.right_v_layout.setStretch(1, 1)
        self.right_v_layout.setStretch(2, 2)
        self.right_v_layout.setStretch(3, 1)

        # self.right_widget.setFixedWidth(200)
        self.main_h_layout.addWidget(self.right_widget)

        self.main_image_view.object_menu = \
            self.r_object_list_widget.list_widget.menu

        self.main_h_layout.setStretch(0, 0)
        self.main_h_layout.setStretch(1, 8)
        self.main_h_layout.setStretch(2, 1)

    def __init_menu(self):
        self.__init_menu_window()
        self.__init_menu_file()
        self.__init_menu_edit()
        self.__init_menu_file_list()
        self.__init_menu_frame()
        self.__init_menu_rect()
        self.__init_menu_settings()
        self.__init_menu_help()

        self.__init_menu_widget()

    def __init_menu_window(self):
        # Window Menu
        pass

    def __init_menu_file(self):
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

        self.menu_file_restore_current = \
            QAction(
                "Restore", self.menu_file
            )
        self.menu_file_restore_current.setIcon(
            QIcon(":/menu/preview/file_restore")
        )
        self.menu_file_restore_current.triggered.connect(self.__action_window_restore_current)
        self.menu_file.addAction(self.menu_file_restore_current)

        self.menu_file_restore_before = \
            QAction(
                "   Restore Before", self.menu_file
            )
        self.menu_file_restore_before.setIcon(
            QIcon(":/menu/preview/file_restore")
        )
        self.menu_file_restore_before.triggered.connect(self.__action_window_restore_before)
        self.menu_file.addAction(self.menu_file_restore_before)

        self.menu_file_restore_after = \
            QAction(
                "   Restore After", self.menu_file
            )
        self.menu_file_restore_after.setIcon(
            QIcon(":/menu/preview/file_restore")
        )
        self.menu_file_restore_after.triggered.connect(self.__action_window_restore_after)
        self.menu_file.addAction(self.menu_file_restore_after)

        self.menu_file_restore_all = \
            QAction(
                "   Restore All", self.menu_file
            )
        self.menu_file_restore_all.setIcon(
            QIcon(":/menu/preview/file_restore")
        )
        self.menu_file_restore_all.triggered.connect(self.__action_window_restore_all)
        self.menu_file.addAction(self.menu_file_restore_all)

        self.menu_file.addSeparator()

        self.menu_file_save_current = \
            QAction(
                "Save", self.menu_file
            )
        self.menu_file_save_current.setIcon(
            QIcon(":/menu/preview/file_save")
        )
        self.menu_file_save_current.triggered.connect(self.__action_window_save_current)
        self.menu_file.addAction(self.menu_file_save_current)

        self.menu_file_save_before = \
            QAction(
                "   Save Before", self.menu_file
            )
        self.menu_file_save_before.setIcon(
            QIcon(":/menu/preview/file_save")
        )
        self.menu_file_save_before.triggered.connect(self.__action_window_save_before)
        self.menu_file.addAction(self.menu_file_save_before)

        self.menu_file_save_after = \
            QAction(
                "   Save After", self.menu_file
            )
        self.menu_file_save_after.setIcon(
            QIcon(":/menu/preview/file_save")
        )
        self.menu_file_save_after.triggered.connect(self.__action_window_save_after)
        self.menu_file.addAction(self.menu_file_save_after)

        self.menu_file_save_all = \
            QAction(
                "   Save All", self.menu_file
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

    def __init_menu_edit(self):
        # Edit Menu
        self.menu_edit = self.menu.addMenu("Edit")

        self.menu_edit_unselect_all = \
            QAction(
                "Unselect All", self.menu_edit
            )
        self.menu_edit_unselect_all \
            .triggered.connect(self.__action_obj_unselect_all)
        self.menu_edit.addAction(self.menu_edit_unselect_all)

    def __init_menu_file_list(self):
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

    def __init_menu_frame(self):
        # Frame Menu
        self.menu_frame = self.menu.addMenu("Frame")

        action_group_frame_display_type = QActionGroup(self.menu_frame)

        # Original
        self.action_group_frame_display_type_radio_original = \
            MenuItemRadio(
                "Original Image",
                parent=action_group_frame_display_type,
                action_group=action_group_frame_display_type,
                menu=self.menu_frame
            )
        self.action_group_frame_display_type_radio_original \
            .triggered.connect(self.__action_frame_display_type_changed)

        # Outline
        self.action_group_frame_display_type_radio_outline = \
            MenuItemRadio(
                "Outline",
                parent=action_group_frame_display_type,
                action_group=action_group_frame_display_type,
                menu=self.menu_frame
            )
        self.action_group_frame_display_type_radio_outline \
            .triggered.connect(self.__action_frame_display_type_changed)

        # Outline + Binary
        self.action_group_frame_display_type_radio_outline_binary = \
            MenuItemRadio(
                "Outline(Binary)",
                parent=action_group_frame_display_type,
                action_group=action_group_frame_display_type,
                menu=self.menu_frame
            )
        self.action_group_frame_display_type_radio_outline_binary \
            .triggered.connect(self.__action_frame_display_type_changed)

        self.menu_frame_outline_binary_threshold = \
            QAction("   Set 'Binary Threshold Value'", parent=self.menu_frame)
        self.menu_frame_outline_binary_threshold.triggered.connect(
            self.__action_set_frame_outline_binary_threshold
        )
        self.menu_frame.addAction(self.menu_frame_outline_binary_threshold)

        # Adjustment
        self.action_group_frame_display_type_radio_adjustment = \
            MenuItemRadio(
                "Contrast and Brightness Adjustment",
                parent=action_group_frame_display_type,
                action_group=action_group_frame_display_type,
                menu=self.menu_frame
            )
        self.action_group_frame_display_type_radio_adjustment \
            .triggered.connect(self.__action_frame_display_type_changed)
        self.menu_frame_set_brightness_contrast = \
            QAction("   Set `Brightness` and `Contrast`", parent=self.menu_frame)
        self.menu_frame_set_brightness_contrast.triggered.connect(
            self.__action_set_frame_brightness_contrast
        )
        self.menu_frame.addAction(self.menu_frame_set_brightness_contrast)

        self.action_group_frame_display_type_radio_original.setChecked(True)

        self.menu_frame.addSeparator()

        self.action_frame_fix_all = \
            QAction("Fix All", self.menu_frame)
        self.action_frame_fix_all.triggered.connect(self.__action_frame_fix_all)
        self.menu_frame.addAction(self.action_frame_fix_all)

    def __init_menu_rect(self):
        # Rect Menu
        self.menu_rect = self.menu.addMenu("Rect")

        # Show Box
        self.menu_rect_show_box = \
            QAction("Show Box", self.menu_frame)
        self.menu_rect_show_box.setCheckable(True)
        self.menu_rect_show_box.setChecked(program_settings.menu_rect_show_box)
        self.menu_rect_show_box.triggered.connect(
            lambda x: self.__action_frame_show_box()
        )
        self.menu_rect.addAction(self.menu_rect_show_box)

        # Show Box Label
        self.menu_rect_show_box_label = \
            QAction("Show Box Label", self.menu_frame)
        self.menu_rect_show_box_label.setCheckable(True)
        self.menu_rect_show_box_label.setChecked(program_settings.menu_rect_show_box_label)
        self.menu_rect_show_box_label.triggered.connect(
            lambda x: self.__action_frame_show_box_label()
        )
        self.menu_rect.addAction(self.menu_rect_show_box_label)

        # Only Show Selected
        self.menu_rect_only_show_selected = \
            QAction("Only Show Selected (Zen Mode)", self.menu_frame)
        self.menu_rect_only_show_selected.setCheckable(True)
        self.menu_rect_only_show_selected.setChecked(program_settings.menu_rect_only_show_selected)
        self.menu_rect_only_show_selected.triggered.connect(
            lambda x: self.__action_frame_set_only_show_selected()
        )
        self.menu_rect.addAction(self.menu_rect_only_show_selected)

        self.menu_rect.addSeparator()

        self.menu_rect_add_rect = \
            QAction("Add Rect", self.menu_frame)
        self.menu_rect_add_rect.triggered.connect(self.__action_rect_add_rect)
        self.menu_rect.addAction(self.menu_rect_add_rect)

    def __init_menu_settings(self):
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

    def __init_menu_help(self):
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

    def __init_menu_widget(self):
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
        self.r_object_list_widget.menu_copy_subsequent \
            .triggered.connect(self.__action_obj_copy_subsequent_target)

        self.r_object_list_widget.menu_operate_del \
            .triggered.connect(self.__action_obj_del_target)
        self.r_object_list_widget.menu_operate_del_subsequent \
            .triggered.connect(self.__action_obj_del_subsequent_target)
        self.r_object_list_widget.menu_operate_del_between \
            .triggered.connect(self.__action_obj_del_between_target)

        self.r_object_list_widget.menu_unselect_all \
            .triggered.connect(self.__action_obj_unselect_all)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        modifiers = event.modifiers()
        key = event.key()

        match modifiers:
            case Qt.KeyboardModifier.NoModifier:
                pass

            case Qt.KeyboardModifier.ControlModifier:
                pass

            case Qt.KeyboardModifier.AltModifier:
                # Alt
                match key:
                    case Qt.Key.Key_1:
                        self.action_group_frame_display_type_radio_original.setChecked(True)
                        self.__action_frame_display_type_changed()
                        return
                    case Qt.Key.Key_2:
                        self.action_group_frame_display_type_radio_outline.setChecked(True)
                        self.__action_frame_display_type_changed()
                        return
                    case Qt.Key.Key_3:
                        self.action_group_frame_display_type_radio_outline_binary.setChecked(True)
                        self.__action_frame_display_type_changed()
                        return
                    case Qt.Key.Key_4:
                        self.action_group_frame_display_type_radio_adjustment.setChecked(True)
                        self.__action_frame_display_type_changed()
                        return
                    case Qt.Key.Key_H:
                        self.menu_rect_show_box.setChecked(not self.menu_rect_show_box.isChecked())
                        self.__action_frame_show_box()
                        return

    def update(self):
        super().update()

        self.setWindowTitle(
            self.basic_window_title + " - " + self.work_directory_path
        )
        # self.label_work_path.setText(
        #     "Work Directory: " + self.work_directory_path
        # )

    def load_directory(self, reload: bool = False):
        # Clear
        self.current_file_str_list.clear()
        self.r_object_list_widget.list_widget.clear()

        self.annotation_directory.dir_path = self.work_directory_path

        if reload or not self.annotation_directory.walked:
            logger.info("Annotation Directory Walk Dir")
            self.annotation_directory.walk_dir()

        self.annotation_directory.sort_path(group_directory=True)

        if reload or not self.annotation_directory.loaded:
            logger.info("Annotation Directory Load Json Files")
            self.annotation_directory.load_json_files()

        self.annotation_directory.update_label_list()

        self.only_file_name = self.annotation_directory.can_only_file_name

        self.__update_label_list()
        self.__update_file_list()

    def __update_label_list(self):
        # Update Label List
        self.r_label_class_list_widget.list_widget.clear()
        for label_name in self.annotation_directory.label_list:
            self.r_label_class_list_widget.list_widget.addItem(label_name)
        self.r_label_class_list_widget.list_widget.addItem("Disable Filter")
        self.r_label_class_list_widget.update()

    def __update_file_list(self):
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

        self.update_detail_info()

    def update_file_list_widget(self):
        annotation_obj_list: List[XAnyLabelingAnnotation] = \
            self.current_file_list

        current_selected_text = self.r_file_list_widget.selection_text

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

        # Restore Selection
        index = -1
        for i, file_name in enumerate(self.current_file_str_list):
            if file_name == current_selected_text:
                index = i
                break
        if index != -1:
            self.r_file_list_widget.selection_index = index

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

        self.previous_annotation_object = None
        if index != 0:
            self.previous_annotation_object = self.annotation_directory.annotation_file[index - 1]

        self.main_image_view.update_dataset_annotation_path(
            annotation_obj=self.current_annotation_object,
            previous_annotation_obj=self.previous_annotation_object
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
        self.update_detail_info()

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

        self.update_detail_info()

    def __slot_property_changed(self):
        self.menu_rect_show_box.setChecked(self.main_image_view.show_box)
        self.menu_rect_show_box_label.setChecked(self.main_image_view.show_box_label)

    def save_current_opened(self):
        if self.current_annotation_object is not None:
            if self.current_annotation_object.save():
                self.__successful_saved(self.current_annotation_object)

    def __action_window_restore_current(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to restore current?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_annotation_object.reload()
            self.__update_object_list_widget()
            self.update_detail_info()

    def __action_window_restore_before(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to restore before?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        have_file_reload = False
        if reply == QMessageBox.StandardButton.Yes:
            file_index = self.get_current_file_truly_index()
            for i, annotation in enumerate(self.annotation_directory.annotation_file):
                if i < file_index:
                    if annotation.reload():
                        have_file_reload = True
                else:
                    break

            self.__update_object_list_widget()

        return have_file_reload

    def __action_window_restore_after(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to restore after?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        have_file_reload = False
        if reply == QMessageBox.StandardButton.Yes:
            file_index = self.get_current_file_truly_index()
            for i, annotation in enumerate(self.annotation_directory.annotation_file):
                if i > file_index:
                    if annotation.reload():
                        have_file_reload = True
                else:
                    continue

            self.__update_object_list_widget()

        return have_file_reload

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

    def __action_window_save_current(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to save current file?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_annotation_object.save()
            self.__successful_saved(self.current_annotation_object)

    def __action_window_save_before(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to save before?\n"
            "Not include current file.",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        have_saved = False
        if reply == QMessageBox.StandardButton.Yes:
            file_index = self.get_current_file_truly_index()
            for i, annotation in enumerate(self.annotation_directory.annotation_file):
                if i < file_index:
                    if annotation.save():
                        have_saved = True
                        self.__successful_saved(annotation)
                else:
                    break

        return have_saved

    def __action_window_save_after(self):
        reply = QMessageBox.question(
            self,
            "Question",
            "Are you sure you want to save after?\n"
            "Not include current file.",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        have_saved = False
        if reply == QMessageBox.StandardButton.Yes:
            file_index = self.get_current_file_truly_index()
            for i, annotation in enumerate(self.annotation_directory.annotation_file):
                if i > file_index:
                    if annotation.save():
                        have_saved = True
                        self.__successful_saved(annotation)
                else:
                    continue

        return have_saved

    def __action_window_save_all(self) -> bool:
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
            return True

        return False

    def __try_to_exit(self):
        # self.save_current_opened()
        if self.check_is_have_modified():
            self.__action_window_save_all()

        self.close()

    def get_current_file_truly_index(self) -> int:
        current_list_index = self.r_file_list_widget.selection_index
        file_name = self.current_file_str_list[current_list_index]

        all_file_name_list = self.annotation_directory.file_name_list

        file_index = -1
        for i, file_name_str in enumerate(all_file_name_list):
            if file_name_str == file_name:
                file_index = i
                break

        return file_index

    def __action_file_reload(self):
        ok = QMessageBox.question(
            self,
            "Warning",
            "Are you sure you want to reload?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        file_index = self.get_current_file_truly_index()
        if file_index != -1:
            file_obj = self.annotation_directory.annotation_file[file_index]

            file_name = file_obj.file_name_no_extension
            logger.info(f"Reload File: {file_name}")
            file_obj.reload(check=False)

        self.__update_object_list_widget()

    def __get_selection_image_path(self) -> str:
        file_index = self.get_current_file_truly_index()

        if file_index == -1:
            return ""

        file_path = self.annotation_directory.annotation_file[file_index].pic_path

        return file_path

    def __get_selection_json_path(self) -> str:
        file_index = self.get_current_file_truly_index()

        if file_index == -1:
            return ""

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

    def __action_obj_copy_subsequent_target(self):
        if self.r_object_list_widget.selection_index == -1:
            return

        # Get Current Object from Current List
        selected_rect_obj = self.current_annotation_object.rect_annotation_list[
            self.r_object_list_widget.selection_index
        ]

        file_index = self.get_current_file_truly_index()
        if file_index == -1:
            return

        for i, annotation_obj in enumerate(self.annotation_directory.annotation_file):
            if i < file_index:
                continue

            annotation_obj.add_or_update_rect(selected_rect_obj)

    def __action_obj_del_target(self):
        reply = QMessageBox.question(
            self,
            "Warning",
            "Are you sure you want to del target?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        index = self.r_object_list_widget.selection_index

        rect_annotation_list = self.current_annotation_object.rect_annotation_list
        obj = rect_annotation_list[index]
        rect_annotation_list.remove(obj)

        self.current_annotation_object.modifying()

        self.r_object_list_widget.selection_index = -1

        self.__update_object_list_widget()

    def __action_obj_del_subsequent_target(self):
        reply = QMessageBox.question(
            self,
            "Warning",
            "Are you sure you want to del subsequent target?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        file_index = self.get_current_file_truly_index()
        if file_index == -1:
            return

        index = self.r_object_list_widget.selection_index
        logger.info(f"[{index}]Delete the target in subsequent frames(Start from {file_index})")
        label = self.current_annotation_object.rect_annotation_list[index].label
        logger.info(f"Delete Label:{label}")

        # self.current_annotation_object.del_by_label(label)
        for i, annotation_obj in enumerate(self.annotation_directory.annotation_file):
            if i < file_index:
                continue

            annotation_obj.del_by_label(label)

        self.r_object_list_widget.selection_index = -1

        self.__update_object_list_widget()

    def __action_obj_del_between_target(self):
        dialog = DialogInput2Int(
            default_value1=0,
            default_value2=0,
            label1="Start Frame:",
            label2="End Frame:",
            min_value=0,
            max_value=len(self.annotation_directory.annotation_file) - 1,
            title="Delete Target Between Frames",
            parent=self
        )
        dialog.setGeometry(100, 100, 200, 150)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        frame_start, frame_end = dialog.get_integers()

        index = self.r_object_list_widget.selection_index
        logger.info(f"[{index}]Delete the target in range({frame_start}~{frame_end})")
        label = self.current_annotation_object.rect_annotation_list[index].label
        logger.info(f"Delete Label:{label}")

        for i, annotation_obj in enumerate(self.annotation_directory.annotation_file):
            if not (frame_start <= i <= frame_end):
                continue

            annotation_obj.del_by_label(label)

        self.__update_object_list_widget()

    def __action_obj_unselect_all(self):
        self.r_object_list_widget.selection_index = -1

    def __action_frame_display_type_changed(self):
        if self.action_group_frame_display_type_radio_original.isChecked():
            self.__action_frame_display_type(ImageDisplayType.Original)
        elif self.action_group_frame_display_type_radio_outline.isChecked():
            self.__action_frame_display_type(ImageDisplayType.Outline)
        elif self.action_group_frame_display_type_radio_outline_binary.isChecked():
            self.__action_frame_display_type(ImageDisplayType.OutlineBinary)
        elif self.action_group_frame_display_type_radio_adjustment.isChecked():
            self.__action_frame_display_type(ImageDisplayType.Adjustment)
        else:
            self.__action_frame_display_type(ImageDisplayType.Original)

    def __action_frame_display_type(self, type: ImageDisplayType):
        match type:
            case ImageDisplayType.Original:
                # Original Image
                logger.info("Original Image")
                self.main_image_view.image_view.image_display_type = ImageDisplayType.Original
            case ImageDisplayType.Outline:
                # Outline Image
                logger.info("Outline Image")
                self.main_image_view.image_view.image_display_type = ImageDisplayType.Outline
            case ImageDisplayType.OutlineBinary:
                # Outline Binary Image
                logger.info("Outline Binary Image")
                self.main_image_view.image_view.image_display_type = ImageDisplayType.OutlineBinary
            case ImageDisplayType.Adjustment:
                # Adjustment Image
                logger.info("Adjust Image Contrast and Brightness")
                self.main_image_view.image_view.image_display_type = ImageDisplayType.Adjustment
            case _:
                logger.error("Unknown mode")

    def __action_frame_fix_all(self):
        ok = QMessageBox.question(
            self,
            "Warning",
            "Are you sure you want to fix all?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        logger.info("Start to Fix All")
        if self.annotation_directory.fix_bugs():
            logger.info("Fix All have modified")
            self.update_annotation_object_display()

    def __action_set_frame_outline_binary_threshold(self):
        number, ok = QInputDialog.getInt(
            self,
            "Input Dialog",
            "Enter the threshold value:",
            value=self.main_image_view.image_view.outline_binary_threshold
        )
        if ok:
            self.main_image_view.image_view.outline_binary_threshold = number
            self.main_image_view.image_view.update()

    def __action_set_frame_brightness_contrast(self):
        dialog_brightness_contrast = DialogBrightnessContrast(parent=self)

        dialog_brightness_contrast.brightness = self.main_image_view.image_view.image_brightness
        dialog_brightness_contrast.contrast = self.main_image_view.image_view.image_contrast

        dialog_brightness_contrast.slot_brightness_changed.connect(
            lambda x: setattr(
                self.main_image_view.image_view, "image_brightness",
                x
            )
        )
        dialog_brightness_contrast.slot_contrast_changed.connect(
            lambda x: setattr(
                self.main_image_view.image_view, "image_contrast",
                x
            )
        )

        dialog_brightness_contrast.show()

    def __action_frame_show_box(self):
        value = self.menu_rect_show_box.isChecked()

        self.main_image_view.show_box = value

        setattr(
            program_settings, "frame_show_box",
            value
        )

    def __action_frame_show_box_label(self):
        value = self.menu_rect_show_box_label.isChecked()

        self.main_image_view.show_box_label = value

        setattr(
            program_settings, "frame_show_box_label",
            value
        )

    def __action_frame_set_only_show_selected(self):
        value = self.menu_rect_only_show_selected.isChecked()

        self.main_image_view.only_show_selected = value

        setattr(
            program_settings, "menu_rect_only_show_selected",
            value
        )

    def __action_rect_add_rect(self):
        default_label_name: str = ""

        is_digit_label = True
        for exist_label_name in self.annotation_directory.label_list:
            # Check is Digit
            if not exist_label_name.isdigit():
                is_digit_label = False
                break
        if is_digit_label:
            digit_list = [
                int(exist_label_name)
                for exist_label_name in self.annotation_directory.label_list
            ]
            # Max Value
            max_value = max(digit_list)
            default_label_name = str(max_value + 1)

        label_name, ok = QInputDialog.getText(
            self,
            "Input Dialog",
            "Enter the label name:"
            f" (Suggest: {default_label_name})",
            text=default_label_name
        )

        if not ok:
            return

        # Check Label Name is Exist?
        if label_name in self.annotation_directory.label_list:
            ok = QMessageBox.question(
                self,
                "Question",
                "Label name already exists.\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No
            )

            if not ok:
                return

        # Add New Rect
        self.current_annotation_object.add_rect(label_name)

        # Update Display
        self.update_annotation_object_display()

    def update_annotation_object_display(self):
        self.annotation_directory.update_label_list()
        self.__update_label_list()
        self.__update_object_list_widget()
        self.main_image_view.init_annotation_widget()

    def check_is_have_modified(self) -> bool:
        found = False

        for annotation_obj in self.annotation_directory.annotation_file:
            if annotation_obj.is_modified:
                found = True
                logger.info(f"{annotation_obj.file_path} is modified but not save.")

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

    def update_detail_info(self):
        image_rect: ImageRect = self.r_file_detail_widget.image_rect

        img_width = 0
        img_height = 0

        if self.current_annotation_object is not None:
            img_width = \
                self.current_annotation_object.image_width
            img_height = \
                self.current_annotation_object.image_height

        image_rect.img_width = img_width
        image_rect.img_height = img_height

        index = -1
        selected_rect_widget = None
        for i, rect_widget in enumerate(self.main_image_view.annotation_widget_rect_list):
            if rect_widget.selecting:
                index = i
                selected_rect_widget = rect_widget

        ori_x = 0
        ori_y = 0
        ori_w = 0
        ori_h = 0

        if index != -1:
            ori_x = selected_rect_widget.ori_x
            ori_y = selected_rect_widget.ori_y
            ori_w = selected_rect_widget.ori_w
            ori_h = selected_rect_widget.ori_h

        image_rect.rect_x = ori_x
        image_rect.rect_y = ori_y
        image_rect.rect_width = ori_w
        image_rect.rect_height = ori_h

        self.toolkit_widget.update()

    def closeEvent(self, event):
        super().closeEvent(event)

        if not self.check_is_have_modified():
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "File not save",
            "You have not saved some files.\n"
            "Are you sure you want to quit without save?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            if self.__action_window_save_all():
                event.accept()
            else:
                event.ignore()
