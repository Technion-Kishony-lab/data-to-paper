from data_to_paper.utils.operator_value import OperatorValue


class PValue(OperatorValue):

    def __init__(self, value, created_by: str = None):
        super().__init__(value)
        self.created_by = created_by

    def __str__(self):
        return f'PValue({self.value})'
