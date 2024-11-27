from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
)
from PySide6.QtCore import Qt

from mot_toolkit.datatype.dataset.object_classfication import (
    ObjectClassConfigure, ObjectClass
)
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class ClassSelectionDialog(QDialog):
    class_id: str
    object_class_configure: ObjectClassConfigure
    __selected_class_id: str = ""

    def __init__(
            self,
            class_configure: ObjectClassConfigure,
            class_id: str = "",
            parent=None
    ):
        super().__init__(parent)

        self.setWindowTitle("Select Class")

        self.class_id = class_id
        self.object_class_configure = class_configure

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()

        # Create a combo box to list all classes
        self.class_combo_box = QComboBox()
        for obj_class in self.object_class_configure.object_classes:
            self.class_combo_box.addItem(f"ID: {obj_class.class_id} | Name: {obj_class.class_name}", obj_class.class_id)

        # Set the current index if the class_id exists
        index = self.class_combo_box.findData(self.class_id)
        if index != -1:
            self.class_combo_box.setCurrentIndex(index)

        layout.addWidget(QLabel("Select a class:"))
        layout.addWidget(self.class_combo_box)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def accept(self):

        self.selected_class_id = self.class_combo_box.currentData()

        super().accept()

    def reject(self):
        super().reject()

    def keyPressEvent(self, event):
        if (
                event.key() == Qt.Key.Key_Return or
                event.key() == Qt.Key.Key_Enter
        ):
            self.accept()
        else:
            super().keyPressEvent(event)

    @property
    def selected_class_id(self) -> str:
        return self.__selected_class_id


# Example usage
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    # 创建一些示例数据
    object_class_configure = ObjectClassConfigure()
    object_class_configure.object_classes = [
        ObjectClass(class_id="001", class_name="Car"),
        ObjectClass(class_id="002", class_name="Truck"),
        ObjectClass(class_id="003", class_name="Bicycle"),
    ]

    dialog = ClassSelectionDialog(object_class_configure, "002")
    if dialog.exec() == QDialog.DialogCode.Accepted:
        selected_class_id = dialog.selected_class_id
        print(f"Selected Class ID: {selected_class_id}")
    else:
        print("Dialog was canceled")

    app.exec()
