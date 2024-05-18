import json

from mot_toolkit.parser.file_encoding import read_file_with_detect


def parse_json_to_dict(json_path:str)->dict:
    json_str = read_file_with_detect(json_path)
    data = json.loads(json_str)
    return data


if __name__ == '__main__':
    json_dict = parse_json_to_dict(r"H:\LCF\mot-toolkit\Test\00000000.json")
    print(json_dict)
    print(type(json_dict))
