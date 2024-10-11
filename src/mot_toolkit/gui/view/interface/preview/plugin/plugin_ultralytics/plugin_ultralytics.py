from mot_toolkit.gui.view.interface.preview.plugin. \
    base.base_plugin import BasePlugin


class PluginUltralytics(BasePlugin):
    def __init__(self):
        super().__init__()

        self.__setup_plugin()

    def __setup_plugin(self):
        self.plugin_name = "Ultralytics plugin"
        self.plugin_description = "Ultralytics YOLOv8 for MOT Toolkit"
        self.plugin_version = "1.0"
        self.plugin_author = "Haomin Kong"
        self.required_packages = ["torch", "ultralytics"]
