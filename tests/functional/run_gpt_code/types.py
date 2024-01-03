

class TestDoNotAssign:
    def __init__(self):
        self.allowed = 0
        self.not_allowed = 0

    def set_internally(self, value):
        self.not_allowed = value
