import json
import os

from mot_toolkit.parser.file_encoding import read_file_with_detect
from mot_toolkit.utils.logs import get_logger
from mot_toolkit.config.program_path import path_project

logger = get_logger()


def parse_json_to_dict(json_path: str) -> dict:
    json_str = read_file_with_detect(json_path).strip()

    if len(json_str) == 0:
        logger.error(f"Empty JSON file: {json_path}")
        return {}

    data = {}

    try:
        data = json.loads(json_str)
    except json.decoder.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e}")
    except Exception as e:
        logger.error(f"Exception: {e}")

    return data


if __name__ == '__main__':
    json_path = os.path.join(path_project, "Test", "00000000.json")

    json_dict = parse_json_to_dict(json_path)

    print(json_dict)
    print(type(json_dict))
