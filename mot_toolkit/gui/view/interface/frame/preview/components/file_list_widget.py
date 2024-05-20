from mot_toolkit.gui.view. \
    components.list_with_title_widget import ListWithTitleWidget


class FileListWidget(ListWithTitleWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        self.set_title("File List")

    def __init_widgets(self):
        pass
