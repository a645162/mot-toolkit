import os
from enum import Enum


class LinuxWindowSystem(Enum):
    X11 = "X11"
    Wayland = "Wayland"
    Unknown = "Unknown"

    @staticmethod
    def detect() -> "LinuxWindowSystem":
        # Check $XDG_SESSION_TYPE
        if 'XDG_SESSION_TYPE' in os.environ:
            if os.environ['XDG_SESSION_TYPE'] == 'x11':
                return LinuxWindowSystem.X11
            elif os.environ['XDG_SESSION_TYPE'] == 'wayland':
                return LinuxWindowSystem.Wayland

        if 'WAYLAND_DISPLAY' in os.environ:
            return LinuxWindowSystem.Wayland
        elif 'DISPLAY' in os.environ:
            return LinuxWindowSystem.X11

        return LinuxWindowSystem.Unknown


if __name__ == "__main__":
    window_system = LinuxWindowSystem.detect()
    print(f"Current Window System: {window_system}")
