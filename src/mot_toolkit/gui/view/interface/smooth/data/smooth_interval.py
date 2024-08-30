from typing import List

from mot_toolkit.datatype. \
    common.rect_data_annotation import RectDataAnnotation
from mot_toolkit.datatype. \
    xanylabeling import AnnotationFileInterval, XAnyLabelingAnnotation


class SmoothInterval(AnnotationFileInterval):
    __is_checked: bool = False
    __is_valid: bool = False

    error_file_name_list: List[str]
    error_obj_list: List[XAnyLabelingAnnotation]

    def __init__(self):
        super().__init__()

        self.error_file_name_list = []
        self.error_obj_list = []

    @staticmethod
    def from_parent(parent_obj: AnnotationFileInterval) -> "SmoothInterval":
        new_obj = SmoothInterval()
        new_obj.__dict__.update(parent_obj.__dict__)

        return new_obj

    def check(self):
        if self.__is_checked:
            return

        self.__is_checked = True

        self.__is_valid = True

        if not self.first_file.check_annotation_list_is_same(self.last_file):
            self.__is_valid = False
            self.last_file.have_error = True

        self.first_file.check_error()
        self.last_file.check_error()

        for annotation_file_obj in self.other_files_list:
            if not annotation_file_obj.check_annotation_list_is_same(self.first_file):
                self.__is_valid = False
                annotation_file_obj.have_error = True

                continue

            # Basic check
            annotation_file_obj.check_error()

    @property
    def is_valid(self) -> bool:
        if not self.__is_checked:
            self.check()

        return self.__is_valid

    @staticmethod
    def interpolate_position(start_pos, end_pos, num_frames, current_frame_index):
        value = start_pos + (end_pos - start_pos) * current_frame_index / (num_frames - 1)

        # Round to 2 decimal places
        value = round(value, 2)

        return value

    def smooth(self, callback_function: callable):
        def callback_log(log: str):
            log_name = self.name.strip()
            if len(log_name):
                log_name = f"[{log_name}] "
            callback_function(f"{log_name}: {log}")

        def get_annotation_target(file_obj: XAnyLabelingAnnotation, target: str) -> RectDataAnnotation | None:
            annotation_list = \
                file_obj.get_target_name_rect_annotation_list(target)
            if len(annotation_list) == 1:
                return annotation_list[0]

            return None

        if not self.__is_valid:
            callback_log("Invalid interval")
            return

        tag_list = self.first_file.get_tag_list()

        for tag in tag_list:
            first_obj = get_annotation_target(self.first_file, tag)
            last_obj = get_annotation_target(self.last_file, tag)

            if first_obj is None or last_obj is None:
                callback_log(f"{tag} not found in first or last file")
                return

            num_frames = len(self.other_files_list) + 2

            for i, current_file in enumerate(self.other_files_list):
                current_obj = get_annotation_target(current_file, tag)
                if current_obj is None:
                    callback_log(f"{tag} not found in file({current_file.file_name})")
                    return

                # Interpolate x1, x2, y1, y2 for the current frame
                current_obj.x1 = self.interpolate_position(first_obj.x1, last_obj.x1, num_frames, i + 1)
                current_obj.x2 = self.interpolate_position(first_obj.x2, last_obj.x2, num_frames, i + 1)
                current_obj.y1 = self.interpolate_position(first_obj.y1, last_obj.y1, num_frames, i + 1)
                current_obj.y2 = self.interpolate_position(first_obj.y2, last_obj.y2, num_frames, i + 1)

                current_file.modifying()
                current_file.save()

        callback_log(f"Smoothed {len(self.other_files_list)} Frames")
