from mot_toolkit.gui.view.menu.system_menu import SystemMenu

system_menu = None


def init_system_menu(parent=None, current_menubar=None) -> SystemMenu:
    global system_menu
    if system_menu is None:
        system_menu = SystemMenu(
            parent=parent,
            current_menubar=current_menubar
        )
    return system_menu
