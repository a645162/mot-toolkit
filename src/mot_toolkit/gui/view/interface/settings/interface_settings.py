from mot_toolkit.gui.view.components. \
    window.base_q_main_window import BaseQMainWindow


class PreferenceWindow(BaseQMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Preference")
        self.resize(800, 600)

        self.__init_widgets()

    def __init_widgets(self):
        pass
