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

    def __init__(self, label: str = ""):
        super().__init__()

        self.label = label

    def check_file_is_exist(self) -> bool:
        return os.path.exists(self.file_path)

    def check_pic_is_exist(self) -> bool:
        filename = os.path.basename(self.file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        directory = os.path.dirname(self.file_path)

        for ext in final_image_extension:
            image_path = os.path.join(directory, f"{filename_no_ext}{ext}")
            if os.path.exists(image_path):
                return True
        return False
