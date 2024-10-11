class BasePlugin:
    __plugin_name: str = ""
    __plugin_description: str = ""

    __image_path: str = ""
    __image_width: int = 0
    __image_height: int = 0

    def __init__(self):
        pass

    def __setup_plugin(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    @property
    def plugin_name(self) -> str:
        return self.__plugin_name

    @plugin_name.setter
    def plugin_name(self, value: str):
        if self.__plugin_name != "":
            return
        self.__plugin_name = value

    @property
    def plugin_description(self) -> str:
        return self.__plugin_description

    @plugin_description.setter
    def plugin_description(self, value: str):
        if self.__plugin_description != "":
            return
        self.__plugin_description = value
