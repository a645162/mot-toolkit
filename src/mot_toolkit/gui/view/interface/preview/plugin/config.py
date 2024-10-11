from typing import List

from mot_toolkit.gui.view.interface.preview.plugin. \
    base.base_plugin import BasePlugin
from mot_toolkit.gui.view.interface.preview.plugin. \
    plugin_ultralytics.plugin_ultralytics import PluginUltralytics

plugin_list: List[BasePlugin] = []


def init_plugins():
    plugin_list.append(PluginUltralytics())


def get_plugin_list() -> List[BasePlugin]:
    return plugin_list


def get_plugin_names() -> List[str]:
    return [plugin.plugin_name for plugin in plugin_list]


def get_plugin_by_name(name: str) -> BasePlugin | None:
    for plugin in plugin_list:
        if plugin.plugin_name == name:
            return plugin
    return None
