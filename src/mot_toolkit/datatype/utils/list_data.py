from typing import List


def sort_int_str_list(
        original_list: List[str],
        reverse=False
) -> List[str]:
    original_list_int = [int(i) for i in original_list]
    original_list_int.sort(reverse=reverse)
    original_list = [str(i) for i in original_list_int]

    return original_list
