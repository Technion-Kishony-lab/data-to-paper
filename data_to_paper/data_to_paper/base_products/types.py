from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Union

import pandas as pd

from data_to_paper.code_and_output_files.file_view_params import ContentView
from data_to_paper.latex.clean_latex import wrap_as_latex_code_output
from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.mutable import Mutable
from data_to_paper.code_and_output_files.referencable_text import NumericReferenceableText, \
    hypertarget_if_referencable_text


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: Optional[Union[str, NumericReferenceableText]] = None  # a user provided description of the file
    originated_from: Optional[str] = None  # None for raw file
    is_binary: Optional[bool] = None  # None for auto based on file extension

    def get_is_binary(self):
        """
        Return True if the file is binary.
        """
        if self.is_binary is not None:
            return self.is_binary
        text_exts = ['.txt', '.md', '.csv', '.xls', '.xlsx']
        return Path(self.file_path).suffix not in text_exts

    def is_excel(self):
        return Path(self.file_path).suffix in ['.xlsx', '.xls']

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file (if they exist).
        """
        if self.is_excel():
            # go over all sheets and return all of them:
            df = pd.read_excel(self.file_path, sheet_name=None)
            s = f'This is an Excel file with {len(df)} sheets:\n\n'
            for sheet_name in df.keys():
                s += f'### Sheet: "{sheet_name}"\n'
                s += f'```output\n{df[sheet_name].head(num_lines).to_string(index=False)}\n```\n'
            s += '\n'
            return s

        with open(self.file_path) as f:
            head = []
            for _ in range(num_lines):
                try:
                    head.append(next(f))
                except StopIteration:
                    break
                except UnicodeDecodeError:
                    head.append('UnicodeDecodeError\n')
            return f'Here are the first few lines of the file:\n' \
                   f'```output\n{"".join(head)}\n```\n'


    def pretty_repr(self, num_lines: int = 4, content_view: ContentView = None):
        s = f'"{self.file_path}"\n'
        description = self.description
        if description is not None:
            description = hypertarget_if_referencable_text(description, content_view)
            s += f'{description}\n\n'
        if num_lines > 0 and not self.get_is_binary():
            s += self.get_file_header(num_lines)
        return s


class DataFileDescriptions(List[DataFileDescription]):
    """
    A list of data file descriptions.
    """

    def __init__(self, *args, data_folder: Optional[Union[str, Path]] = None,
                 general_description: Optional[Union[str, NumericReferenceableText]] = None,
                 **kwargs):
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

    def get_pretty_description_for_file_and_children(
            self, data_file: DataFileDescription, index: Mutable = None, content_view: ContentView = None):
        """
        Return a pretty description for the given data file and all its children.
        """
        children = self.get_children(data_file)
        index.val += 1
        s = f"File #{index.val}: {data_file.pretty_repr(0 if children else 4, content_view=content_view)}\n"
        for child in children:
            s += self.get_pretty_description_for_file_and_children(child, index)
        return s

    def pretty_repr(self, num_lines: int = 4, content_view: ContentView = None) -> str:
        s = ''
        if self.general_description is not None:
            s += hypertarget_if_referencable_text(self.general_description, content_view) + '\n\n'
        with run_in_directory(self.data_folder):
            if len(self) == 0:
                s += 'No data files'
            elif len(self) == 1:
                s += "1 data file:\n\n"
                s += self[0].pretty_repr(num_lines, content_view=content_view)
            else:
                s += f"{len(self)} data files:\n"
                index = Mutable(0)
                for parent in self.get_all_raw_files():
                    s += self.get_pretty_description_for_file_and_children(parent, index, content_view=content_view)
            return s

    def get_data_filenames(self):
        return [data_file_description.file_path for data_file_description in self]

    def to_latex(self,
                 section_name: str = 'Data Description',
                 label: str = 'sec:data_description',
                 text: str = 'Here is the data description, as provided by the user:',
                 content_view: ContentView = None) -> str:
        s = ''
        s += f"\\section{{{section_name}}} \\label{{{label}}} {text}"
        s += '\n\n' + wrap_as_latex_code_output(
            self.pretty_repr(num_lines=0, content_view=content_view))
        return s
