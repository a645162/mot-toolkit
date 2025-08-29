from typing import Union

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QGridLayout,
    QDialogButtonBox, QWidget, QLineEdit, QLabel, QMessageBox
)


class LabeledLineEdit(QWidget):
    """
    A widget that combines a QLabel and a QLineEdit into a single component.
    """

    def __init__(self, label_text, default_value: Union[str, int, float] = "1.0", parent=None):
        super().__init__(parent)

        # Check if the default value is of a valid type
        if not isinstance(default_value, (str, int, float)):
            raise TypeError("default_value must be a string, int, or float.")

        # Create the label and line edit
        self.label = QLabel(label_text)
        self.line_edit = QLineEdit(str(default_value))

        # Set up layout to hold the label and line edit
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.setContentsMargins(0, 0, 0, 0)  # This removes margins for tight layout

        # Set the layout for this widget
        self.setLayout(layout)

    def get_value(self):
        # Returns the current text in the QLineEdit as a float
        try:
            return float(self.line_edit.text())
        except ValueError:
            return None

    def set_value(self, value):
        # Sets the text in the QLineEdit
        self.line_edit.setText(str(value))


class PaddingInputDialog(QDialog):
    """
    A custom widget to input padding values (top, bottom, left, right) as floating point numbers.
    This widget can be used in a dialog with OK and Cancel buttons.
    """

    def __init__(self, default_values=(0, 0, 0, 0), parent=None):
        super().__init__(parent)

        # Initialize default padding values in the new order: top, bottom, left, right
        (
            self.default_padding_top,
            self.default_padding_bottom,
            self.default_padding_left,
            self.default_padding_right
        ) = default_values

        # Create instances of LabeledLineEdit for each padding value
        self.padding_top_widget = LabeledLineEdit("Padding Top:", self.default_padding_top)
        self.padding_bottom_widget = LabeledLineEdit("Padding Bottom:", self.default_padding_bottom)
        self.padding_left_widget = LabeledLineEdit("Padding Left:", self.default_padding_left)
        self.padding_right_widget = LabeledLineEdit("Padding Right:", self.default_padding_right)

        # Set up grid layout for padding inputs
        grid_layout = QGridLayout()

        # Place widgets in a 3x3 grid layout, adjusting positions for the new order
        grid_layout.addWidget(self.padding_top_widget, 0, 1, 1, 1)
        # Top: middle row, center column

        grid_layout.addWidget(self.padding_bottom_widget, 2, 1, 1, 1)
        # Bottom: bottom row, center column

        grid_layout.addWidget(self.padding_left_widget, 1, 0, 1, 1)
        # Left: center row, left column

        grid_layout.addWidget(self.padding_right_widget, 1, 2, 1, 1)
        # Right: center row, right column

        # Add spacers or empty widgets to maintain layout structure
        grid_layout.addWidget(QWidget(), 0, 0)
        # Top-left corner

        grid_layout.addWidget(QWidget(), 0, 2)
        # Top-right corner

        grid_layout.addWidget(QWidget(), 2, 0)
        # Bottom-left corner

        grid_layout.addWidget(QWidget(), 2, 2)
        # Bottom-right corner

        # Create button box with OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # Connect Ok button to validate_and_accept
        button_box.accepted.connect(self.validate_and_accept)

        # Connect Cancel button to reject
        button_box.rejected.connect(self.reject)

        # Set up main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(grid_layout)
        main_layout.addWidget(button_box)

        # Set the main layout for this dialog
        self.setLayout(main_layout)

        # Set window title
        self.setWindowTitle("Padding Input Dialog")

    def validate_and_accept(self):
        # Validates all padding values and accepts the dialog if they are valid
        # Shows an error message if any value is invalid
        padding_values = self.get_padding_values()
        if all(isinstance(value, float) for value in padding_values):
            self.accept()  # Close the dialog if all values are valid floats
        else:
            QMessageBox.critical(self, "Invalid Input", "All padding values must be valid numbers.")
            # Keep the dialog open by not calling self.accept()

    def get_padding_values(self):
        # Returns the current padding values as a tuple of floats in the new order: top, bottom, left, right
        try:
            return (
                self.padding_top_widget.get_value(),
                self.padding_bottom_widget.get_value(),
                self.padding_left_widget.get_value(),
                self.padding_right_widget.get_value()
            )
        except ValueError:
            # Handle case where text cannot be converted to float
            return None


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dialog = PaddingInputDialog()

    if dialog.exec() == QDialog.DialogCode.Accepted:
        padding_values = dialog.get_padding_values()
        print(f"Selected padding values: {padding_values}")
    else:
        print("Dialog was cancelled.")

    sys.exit(app.exec())
