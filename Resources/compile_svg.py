from typing import List
import os

import cairosvg


def get_jpg_path(svg_path):
    return os.path.splitext(svg_path)[0] + '.jpg'


def svg_to_jpg(
        svg_path, jpg_path,
        width: int = 0,
        height: int = 0,
        over_write=False
):
    if not isinstance(svg_path, str) or not isinstance(jpg_path, str):
        raise ValueError("Path is not a string.")

    if not os.path.exists(svg_path):
        raise FileNotFoundError("SVG file not found.")

    if not over_write and os.path.exists(jpg_path):
        return

    cairosvg.svg2png(
        url=svg_path, write_to=jpg_path,
        output_width=width, output_height=height
    )


def find_svg_files_recursively(directory) -> List[str]:
    svg_files = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.svg'):
                svg_files.append(
                    os.path.abspath(
                        os.path.join(root, file)
                    )
                )

    return svg_files


if __name__ == '__main__':
    svg_path_list = find_svg_files_recursively('./')

    for svg_path in svg_path_list:
        target_jpg_path = get_jpg_path(svg_path)
        if "Icon" in svg_path:
            svg_to_jpg(
                svg_path,
                target_jpg_path,
                width=24,
                height=24
            )
        else:
            svg_to_jpg(
                svg_path,
                target_jpg_path,
            )
