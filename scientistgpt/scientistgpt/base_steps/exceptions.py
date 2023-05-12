from dataclasses import dataclass

from scientistgpt.exceptions import ScientistGPTException


@dataclass(frozen=True)
class FailedCreatingProductException(ScientistGPTException):
    product_field: str = None

    def __str__(self):
        return f"Failed to create product {self.product_field}."
