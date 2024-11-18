from enum import Enum

from typing import List


# https://docs.ultralytics.com/zh/models/sam-2/#segment-everything
class SamModelType(Enum):
    SAM_2_1_Tiny = "sam2.1_t.pt"
    SAM_2_1_Small = "sam2.1_s.pt"
    SAM_2_1_Base = "sam2.1_b.pt"
    SAM_2_1_Large = "sam2.1_l.pt"
    FAST_SAM_S = "FastSAM-s.pt"
    FAST_SAM_X = "FastSAM-x.pt"


def get_sam_model_list() -> List[str]:
    return [model.value for model in SamModelType]


def get_sam_model_by_name(
        model_name: str = ""
) -> SamModelType:
    for model in SamModelType:
        if model.value == model_name:
            return model

    return SamModelType.SAM_2_1_Large
