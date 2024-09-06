from mot_toolkit.gui.view.menu.system_menu import SystemMenu

system_menu: SystemMenu | None = None


def get_system_menu() -> SystemMenu:
    global system_menu
    return system_menu


def init_system_menu(parent=None, current_menubar=None) -> SystemMenu:
    global system_menu
    if system_menu is None:
        system_menu = SystemMenu(
            parent=parent,
            current_menubar=current_menubar
        )
    return system_menu
