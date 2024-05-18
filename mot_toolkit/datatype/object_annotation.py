class ObjectAnnotation:
    def __init__(self, label: str = ""):
        self.label = label
        self.text = ""

    def __str__(self):
        final_str = " " + self.text
        final_str = self.label + final_str.strip()
        return final_str.strip()

    def __repr__(self):
        return self.label

    def __eq__(self, other):
        return (
                len(self.text) > 0 and
                self.label == other.label
        )

    def __ne__(self, other):
        return self.label != other.label
