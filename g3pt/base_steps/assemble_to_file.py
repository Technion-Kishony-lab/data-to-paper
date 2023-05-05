from dataclasses import dataclass
from pathlib import Path

from .base_products_conversers import BaseProductsHandler


@dataclass
class BaseFileProducer(BaseProductsHandler):

    output_file_path: Path = None

    @property
    def output_folder(self):
        return Path(self.output_file_path).parent

    @property
    def output_filename(self):
        return Path(self.output_file_path).name

    @property
    def output_file_stem(self):
        return Path(self.output_file_path).stem

    def produce(self):
        raise NotImplementedError
