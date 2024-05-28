def match_func(a: int) -> str:
    match a:
        case 1:
            return "1"
        case 2:
            return "2"
        case _:
            return "default"


if __name__ == "__main__":
    for i in range(5):
        print(f"[{i}]{match_func(i)}")
