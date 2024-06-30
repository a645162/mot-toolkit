from mot_toolkit.gui.view. \
    components.list_with_title_widget import ListWithTitleWidget


class LabelClassListWidget(ListWithTitleWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_menu()

    def __setup_widget_properties(self):
        self.set_title("Label(Classes)")
        self.count_offset = -1

    def __init_widgets(self):
        pass

    def __init_menu(self):
        pass
