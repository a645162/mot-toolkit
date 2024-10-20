from PySide6.QtCore import Signal, Qt, QRect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget

from mot_toolkit.datatype.common. \
    rect_data_annotation import RectDataAnnotation
from mot_toolkit.datatype.xanylabeling import XAnyLabelingRect
from mot_toolkit.gui.view.components.widget. \
    rect.resizable_rect import ResizableRect


class AnnotationWidgetRect(ResizableRect):
    slot_selected_object: Signal = Signal(QWidget)

    slot_try_to_select: Signal = Signal(QWidget)
    slot_try_to_show_menu: Signal = Signal(QWidget)

    selecting: bool
    __selecting: bool = False

    __show_box: bool = False
    __show_box_label: bool = False
    __only_show_selected: bool = False
    __label_text: str = ""

    # Theme Settings
    final_theme_color: dict = {
        "light": {
            "normal": {
                "border_color": Qt.GlobalColor.blue,
                "fill_color": Qt.GlobalColor.transparent,

                "opacity": 1.0,
                "opacity_border": 0.7,
                "opacity_fill": 0.1,

                "border_width": 4,
            },
            "selected": {
                "border_color": Qt.GlobalColor.red,
                "fill_color": Qt.GlobalColor.green,

                "opacity": 1.0,
                "opacity_border": 0.45,
                "opacity_fill": 0.2,

                "border_width": 12,
            },
        },
        "dark": {
            "normal": {
                "border_color": Qt.GlobalColor.green,
                "fill_color": Qt.GlobalColor.transparent,

                "opacity": 1.0,
                "opacity_border": 0.7,
                "opacity_fill": 0.1,

                "border_width": 4,
            },
            "selected": {
                "border_color": Qt.GlobalColor.white,
                "fill_color": Qt.GlobalColor.transparent,

                "opacity": 1.0,
                "opacity_border": 0.5,
                "opacity_fill": 0.2,

                "border_width": 12,
            },
        }
    }
    theme_color: dict = {}

    activate_theme_name: str = "light"

    source: XAnyLabelingRect | None = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__init_widget_props()

        self.set_appearance()

    def __init_widget_props(self):
        self.border_width = 8
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def set_rect_data_annotation(self, rect_data: RectDataAnnotation):
        x1, y1 = int(rect_data.x1), int(rect_data.y1)
        width, height = int(rect_data.width), int(rect_data.height)

        self.ori_x = x1
        self.ori_y = y1
        self.ori_w = width
        self.ori_h = height

        self.update()

        # self.x_original = rect_data.x1
        # self.y_original = rect_data.y1
        # self.width_original = rect_data.width
        # self.height_original = rect_data.height

        # print(
        #     x1, y1,
        #     width, height
        # )

        # self.setGeometry(
        #     x1, y1,
        #     width, height
        # )

        # Print current position
        # print(
        #     self.x(), self.y(),
        #     self.width(), self.height()
        # )

    def is_responsible(self) -> bool:
        if not self.__selecting:
            return False

        return True

    def mousePressEvent(self, event):
        match event.button():
            case Qt.MouseButton.LeftButton:
                if not self.is_responsible():
                    return
            case Qt.MouseButton.RightButton:
                if self.resizing:
                    event.ignore()
                    return
                if self.is_responsible():
                    self.slot_try_to_show_menu.emit(self)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if not self.is_responsible():
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_responsible():
                # Try to select
                if not self.__selecting:
                    self.slot_try_to_select.emit(self)

                return

        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.show_box_label:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            painter.setPen(QColor(255, 0, 0))

            # Calc font size by self.width()
            base_width = 100
            base_font_size = 12
            font_size = int(base_font_size * self.now_width / base_width)

            label = self.label_text
            if label:
                font = painter.font()
                font.setPointSize(font_size)
                painter.setFont(font)

                rect = QRect(4, 0, self.width(), self.height())
                painter.drawText(
                    rect,
                    (
                            Qt.AlignmentFlag.AlignTop |
                            Qt.AlignmentFlag.AlignLeft
                    ),
                    label
                )

            painter.end()

    def update(self):
        super().update()

        self.__update_visibility()

    @property
    def selecting(self) -> bool:
        return self.__selecting

    @selecting.setter
    def selecting(self, value: bool):
        self.__selecting = value

        self.set_appearance()

        if self.__selecting:
            self.raise_()
            # self.focusWidget()

    def set_appearance(self):
        theme_name = self.activate_theme_name
        if theme_name not in self.final_theme_color.keys():
            theme_name = "light"

        theme_group: dict = self.final_theme_color[theme_name]

        selecting_key_str = "selected" if self.selecting else "normal"

        theme: dict = theme_group[selecting_key_str]

        if "border_color" in theme_group.keys():
            self.border_color = theme_group["border_color"]
        elif "border_color" in theme.keys():
            self.border_color = theme["border_color"]
        if "fill_color" in theme_group.keys():
            self.fill_color = theme_group["fill_color"]
        elif "fill_color" in theme.keys():
            self.fill_color = theme["fill_color"]

        if "opacity" in theme_group.keys():
            self.global_opacity = theme_group["opacity"]
        elif "opacity" in theme.keys():
            self.global_opacity = theme["opacity"]
        if "opacity_fill" in theme_group.keys():
            self.fill_opacity = theme_group["opacity_fill"]
        elif "opacity_fill" in theme.keys():
            self.fill_opacity = theme["opacity_fill"]
        if "opacity_border" in theme_group.keys():
            self.border_opacity = theme_group["opacity_border"]
        elif "opacity_border" in theme.keys():
            self.border_opacity = theme["opacity_border"]

        if "border_width" in theme_group.keys():
            self.border_width = theme_group["border_width"]
        elif "border_width" in theme.keys():
            self.border_width = theme["border_width"]

        self.update()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        # modifiers = event.modifiers()
        # key = event.key()
        #
        # move_step_value = 5
        #
        # match modifiers:
        #     case Qt.KeyboardModifier.NoModifier:
        #         pass
        #         # match key:
        #         #     case Qt.Key.Key_Up:
        #         #         self.now_y -= move_step_value
        #         #         self.modify()
        #         #         return
        #         #     case Qt.Key.Key_Down:
        #         #         self.now_y += move_step_value
        #         #         self.modify()
        #         #         return
        #         #     case Qt.Key.Key_Left:
        #         #         self.now_x -= move_step_value
        #         #         self.modify()
        #         #         return
        #         #     case Qt.Key.Key_Right:
        #         #         self.now_x += move_step_value
        #         #         self.modify()
        #         #         return
        #     case Qt.KeyboardModifier.ControlModifier:
        #         pass

        if self.parent() is not None:
            self.parent().keyPressEvent(event)

    @property
    def label_text(self) -> str:
        label = self.__label_text.strip()

        if label == "":
            label = self.label

        return label.strip()

    @label_text.setter
    def label_text(self, value: str):
        self.__label_text = value
        self.update()

    @property
    def show_box(self) -> bool:
        return self.__show_box

    @show_box.setter
    def show_box(self, value: bool):
        self.__show_box = value

        self.__update_visibility()

    @property
    def show_box_label(self) -> bool:
        return self.__show_box_label

    @show_box_label.setter
    def show_box_label(self, value: bool):
        self.__show_box_label = value

        self.update()

    @property
    def only_show_selected(self) -> bool:
        return self.__only_show_selected

    @only_show_selected.setter
    def only_show_selected(self, value: bool):
        self.__only_show_selected = value

        self.__update_visibility()

    def check_is_should_show(self) -> bool:
        is_should_show = self.show_box
        if self.only_show_selected and not self.selecting:
            is_should_show = False
        return is_should_show

    def __update_visibility(self):
        if self.check_is_should_show():
            self.show()
        else:
            self.hide()
