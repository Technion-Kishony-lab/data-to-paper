from dataclasses import dataclass
from pathlib import Path

from .base_products_conversers import ProductsHandler


@dataclass
class BaseFileProducer(ProductsHandler):

    output_filename: str = None

    @property
    def output_file_path(self):
        return Path(self.output_directory) / self.output_filename

    @property
    def output_file_stem(self):
        return Path(self.output_file_path).stem
