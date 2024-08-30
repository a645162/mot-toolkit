import chardet


def read_file_with_detect(file_path: str) -> str:
    try:
        file_encoding = detect_file_encoding(file_path)
        with open(file_path, "r", encoding=file_encoding) as f:
            return f.read()
    except Exception:
        return ""


def detect_file_encoding(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        return result['encoding']
    except Exception:
        return "utf-8"


if __name__ == '__main__':
    file_encoding = \
        detect_file_encoding(r"H:\LCF\mot-toolkit\Test\00000000.json")
    print(f"Detected file encoding: {file_encoding}")
