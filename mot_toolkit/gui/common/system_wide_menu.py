from mot_toolkit.gui.view.menu.system_menu import SystemMenu

system_menu = None


def init_system_menu() -> SystemMenu:
    global system_menu
    if system_menu is None:
        system_menu = SystemMenu()
    return system_menu
