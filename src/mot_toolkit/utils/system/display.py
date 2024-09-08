import os
from enum import EnumType


class LinuxWindowSystem(EnumType):
    X11 = "X11"
    Wayland = "Wayland"
    Unknown = "Unknown"

    @staticmethod
    def detect():
        if 'WAYLAND_DISPLAY' in os.environ:
            return LinuxWindowSystem.Wayland
        elif 'DISPLAY' in os.environ:
            return LinuxWindowSystem.X11

        return LinuxWindowSystem.Unknown


if __name__ == "__main__":
    window_system = LinuxWindowSystem.detect()
    print(f"Current Window System: {window_system}")
