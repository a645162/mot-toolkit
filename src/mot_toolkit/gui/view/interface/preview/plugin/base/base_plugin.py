from typing import List

from mot_toolkit.utils.py.pip_utils import check_package_is_installed


class BasePlugin:
    __plugin_name: str = ""
    __plugin_description: str = ""
    __plugin_version: str = ""
    __plugin_author: str = ""

    __image_path: str = ""
    __image_width: int = 0
    __image_height: int = 0

    required_packages: List[str]

    def __init__(self):
        self.required_packages = []

    def __setup_plugin(self):
        pass

    def __str__(self):
        if self.__plugin_name != "":
            return self.__plugin_name
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    @property
    def plugin_name(self) -> str:
        return self.__str__()

    @plugin_name.setter
    def plugin_name(self, value: str):
        if self.__plugin_name != "":
            return
        self.__plugin_name = value.strip()

    @property
    def plugin_description(self) -> str:
        return self.__plugin_description

    @plugin_description.setter
    def plugin_description(self, value: str):
        if self.__plugin_description != "":
            return
        self.__plugin_description = value.strip()

    @property
    def plugin_version(self) -> str:
        return self.__plugin_version

    @plugin_version.setter
    def plugin_version(self, value: str):
        if self.__plugin_version != "":
            return
        self.__plugin_version = value.strip()

    @property
    def plugin_author(self) -> str:
        return self.__plugin_author

    @plugin_author.setter
    def plugin_author(self, value: str):
        if self.__plugin_author != "":
            return
        self.__plugin_author = value.strip()

    def check_environment(self) -> bool:
        for package in self.required_packages:
            if not check_package_is_installed(package):
                return False

        return True
