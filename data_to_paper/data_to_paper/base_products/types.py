from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Union

from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.mutable import Mutable


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: Optional[str] = None  # a user provided description of the file
    originated_from: Optional[str] = None  # None for raw file

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file (if they exist).
        """
        with open(self.file_path) as f:
            head = []
            for _ in range(num_lines):
                try:
                    head.append(next(f))
                except StopIteration:
                    break
            return ''.join(head)

    def pretty_repr(self, num_lines: int = 4):
        s = f'"{self.file_path}"\n'
        if self.description is not None:
            s += f'{self.description}\n\n'
        if num_lines > 0:
            s += f'Here are the first few lines of the file:\n' \
                 f'```output\n{self.get_file_header(num_lines)}\n```\n'
        return s


class DataFileDescriptions(List[DataFileDescription]):
    """
    A list of data file descriptions.
    """

    def __init__(self, *args, data_folder: Optional[Union[str, Path]] = None,
                 general_description: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_folder = data_folder
        self.general_description = general_description

    @classmethod
    def from_other(cls, other: DataFileDescriptions):
        return cls(other, data_folder=other.data_folder, general_description=other.general_description)

    def __str__(self):
        return self.pretty_repr()

    def get_file_description(self, file_path: str) -> DataFileDescription:
        """
        Return the data file description for the given file path.
        """
        for data_file_description in self:
            if data_file_description.file_path == file_path:
                return data_file_description
        raise ValueError(f"Could not find file path {file_path} in data file descriptions.")

    def get_children(self, data_file: DataFileDescription):
        """
        Return the children of the given data file.
        """
        return DataFileDescriptions([data_file_description for data_file_description in self
                                     if data_file_description.originated_from == data_file.file_path],
                                    data_folder=self.data_folder)

    def get_all_raw_files(self):
        """
        Return all the raw files.
        """
        return DataFileDescriptions([data_file_description for data_file_description in self
                                     if data_file_description.originated_from is None],
                                    data_folder=self.data_folder)

    def get_pretty_description_for_file_and_children(self, data_file: DataFileDescription, index: Mutable = None):
        """
        Return a pretty description for the given data file and all its children.
        """
        children = self.get_children(data_file)
        index.val += 1
        s = f"File #{index.val}: {data_file.pretty_repr(0 if children else 4)}\n"
        for child in children:
            s += self.get_pretty_description_for_file_and_children(child, index)
        return s

    def pretty_repr(self, num_lines: int = 4):
        s = ''
        if self.general_description is not None:
            s += self.general_description + '\n\n'
        with run_in_directory(self.data_folder):
            if len(self) == 0:
                s += 'No data files'
            elif len(self) == 1:
                s += "1 data file:\n\n"
                s += self[0].pretty_repr(num_lines)
            else:
                s += f"{len(self)} data files:\n"
                index = Mutable(0)
                for parent in self.get_all_raw_files():
                    s += self.get_pretty_description_for_file_and_children(parent, index)
            return s

    def get_data_filenames(self):
        return [data_file_description.file_path for data_file_description in self]
