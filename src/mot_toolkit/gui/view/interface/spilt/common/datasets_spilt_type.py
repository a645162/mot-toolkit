from enum import Enum


class DatasetSpiltType(Enum):
    Train = "train"
    Val = "val"
    Test = "test"
    All = "all"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def is_train(self) -> bool:
        return self == DatasetSpiltType.Train

    def is_val(self) -> bool:
        return self == DatasetSpiltType.Val

    def is_test(self) -> bool:
        return self == DatasetSpiltType.Test

    def __eq__(self, other):
        if isinstance(other, str):
            other = DatasetSpiltType(other)

        if isinstance(other, DatasetSpiltType):
            return (
                    self.is_train() == other.is_train() and
                    self.is_val() == other.is_val() and
                    self.is_test() == other.is_test()
            )
        else:
            return False
