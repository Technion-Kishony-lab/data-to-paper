from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class CodeAndOutput:
    code: str = None
    output: str = None
    output_file: Optional[str] = None
    code_name: str = None
    explanation: Optional[str] = None


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: str  # a user provided description of the file

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file.
        """
        with open(self.file_path) as f:
            head = [next(f) for _ in range(num_lines)]
            return ''.join(head)

    def pretty_repr(self):
        return f'{self.file_path}\n{self.description}\n' \
               f'Here are the first few lines of the file:\n' \
               f'```\n{self.get_file_header()}\n```'


class DataFileDescriptions(List[DataFileDescription]):
    """
    A list of data file descriptions.
    """

    def __str__(self):
        if len(self) == 0:
            s = 'No data files'
        elif len(self) == 1:
            s = "1 data file:\n\n"
            s += self[0].pretty_repr()
        else:
            s = f"{len(self)} data files:\n"
            for file_number, data_file_description in enumerate(self):
                s += f"\n({file_number + 1}) " + data_file_description.pretty_repr()

        return s


@dataclass
class Products(ABC):
    """
    Contains the different outcomes of the process.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """

    @abstractmethod
    def get_description(self, product_field: str) -> str:
        """
        Return the description of the given product.
        """
        pass

    @abstractmethod
    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        pass
