from data_to_paper.exceptions import TerminateException


class FailedCreatingProductException(TerminateException):
    reason: str

    def __str__(self):
        return self.reason
