import sys


def match_func(a: int) -> str:
    # Check Python Version
    if sys.version_info.major < 3 or sys.version_info.minor < 10:
        if a == 1:
            return "1"
        elif a == 2:
            return "2"
        elif a in [3, 4]:
            return "3,4"
        else:
            return "default"
    else:
        match a:
            case 1:
                return "1"
            case 2:
                return "2"
            case [3, 4]:
                return "3,4"
            case _:
                return "default"


if __name__ == "__main__":
    for i in range(5):
        print(f"[{i}]{match_func(i)}")
