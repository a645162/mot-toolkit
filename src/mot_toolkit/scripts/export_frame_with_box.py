import os

import cv2

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory

"""
ffmpeg -framerate 60 -i %08d.jpg -c:v h264_amf -pix_fmt yuv420p output.mp4
ffmpeg -framerate 30 -i 00000000-00000268_box/%08d.jpg -c:v h264_amf -pix_fmt yuv420p output.mp4

"""

def handle_dir(dir_path):
    if not os.path.exists(dir_path):
        return

    dir_name = os.path.basename(dir_path)
    parent_path = os.path.dirname(dir_path)

    save_dir = os.path.join(parent_path, dir_name + "_box")
    os.makedirs(save_dir, exist_ok=True)

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    for annotation_file in annotation_directory.annotation_file:
        name = annotation_file.file_name_no_extension
        image = annotation_file.get_cv_mat_with_box()

        if image is None:
            print(f"Failed to load image: {name}")
            continue
        cv2.imwrite(os.path.join(save_dir, name + ".jpg"), image)

        # cv2.imshow('image', image)
        # cv2.waitKey(1)


if __name__ == '__main__':
    handle_dir('/home/konghaomin/BV1bF411z7nK-2OJs5XeOn2rSXOri/00000000-00000268')
