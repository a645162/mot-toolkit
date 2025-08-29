from enum import Enum


def get_object_area(
        width: int | float,
        height: int | float,
) -> int:
    return int(width * height)


class ObjectSizeType(Enum):
    SMALL = 0
    MEDIUM = 1
    LARGE = 2

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name.title()

    @staticmethod
    def get_coco_object_size_type(
            width: int | float,
            height: int | float,
    ) -> "ObjectSizeType":
        area = get_object_area(width, height)

        if area < 32 * 32:
            return ObjectSizeType.SMALL
        elif area < 96 * 96:
            return ObjectSizeType.MEDIUM
        else:
            return ObjectSizeType.LARGE
