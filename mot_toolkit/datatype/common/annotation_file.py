import os

image_extension = [".jpg", ".png", ".jpeg", ".bmp"]

final_image_extension = []

for ext in image_extension:
    ext = ext.strip().lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    final_image_extension.append(ext)


class AnnotationFile:
    label: str = ""

    file_path: str = ""

    pic_path: str
    __pic_path: str = ""

    def __init__(self, label: str = ""):
        super().__init__()

        self.label = label

    def check_file_is_exist(self) -> bool:
        return os.path.exists(self.file_path)

    def __get_pic_path(self) -> str:
        filename = os.path.basename(self.file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        directory = os.path.dirname(self.file_path)

        for ext in final_image_extension:
            image_path = os.path.join(directory, f"{filename_no_ext}{ext}")
            if os.path.exists(image_path):
                return image_path

        return ""

    @property
    def pic_path(self) -> str:
        if not os.path.exists(self.__pic_path):
            self.__pic_path = self.__get_pic_path()

        if not os.path.exists(self.__pic_path):
            return ""

        return self.__pic_path

    def check_pic_is_exist(self) -> bool:
        return self.pic_path != ""
