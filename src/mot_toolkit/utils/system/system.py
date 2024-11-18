from enum import Enum


class SystemType(Enum):
    Windows = "Windows"
    macOS = "macOS"
    Linux = "Linux"
    Unknown = "Unknown"

    @staticmethod
    def get_system_type() -> "SystemType":
        import sys

        # match sys.platform:
        #     case "win32":
        #         return SystemType.Windows
        #     case "darwin":
        #         return SystemType.macOS
        #     case "linux" | "linux2":
        #         # Python 2的Linux平台标识为'linux2'
        #         return SystemType.Linux
        #     case _:
        #         return SystemType.Unknown

        # Support old version Python
        if sys.platform == "win32":
            return SystemType.Windows
        elif sys.platform == "darwin":
            return SystemType.macOS
        elif sys.platform == "linux" or sys.platform == "linux2":
            return SystemType.Linux
        else:
            return SystemType.Unknown
