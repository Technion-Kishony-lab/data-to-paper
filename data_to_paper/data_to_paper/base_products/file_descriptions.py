from __future__ import annotations

import os
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Union

import pandas as pd

from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.latex.clean_latex import wrap_as_latex_code_output
from data_to_paper.utils.file_utils import run_in_directory, clear_directory
from data_to_paper.utils.mutable import Mutable
from data_to_paper.code_and_output_files.referencable_text import NumericReferenceableText, \
    hypertarget_if_referencable_text_product, ReferencableTextProduct

TEXT_EXTS = ['.txt', '.md', '.csv', '.xls', '.xlsx']


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: Optional[Union[str, ReferencableTextProduct]] = None  # a user provided description of the file
    originated_from: Optional[str] = None  # None for raw file
    is_binary: Optional[bool] = None  # None for auto based on file extension

    def get_is_binary(self):
        """
        Return True if the file is binary.
        """
        if self.is_binary is not None:
            return self.is_binary

        return Path(self.file_path).suffix not in TEXT_EXTS

    def is_excel(self):
        return Path(self.file_path).suffix in ['.xlsx', '.xls']

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file (if they exist).
        """
        if self.is_excel():
            # go over all sheets and return all of them:
            df = pd.read_excel(self.file_path, sheet_name=None)
            s = f'This is an Excel file with {len(df)} sheets. Here is the first few rows for each sheet:\n\n'
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

    def pretty_repr(self, num_lines: int = 4, view_purpose: ViewPurpose = None, file_num: Optional[int] = None) -> str:
        if file_num is not None:
            s = f'### File {file_num}: "{self.file_path}"\n'
        else:
            s = f'### "{self.file_path}"\n'
        description = self.description
        if description is not None:
            description = hypertarget_if_referencable_text_product(description, view_purpose, with_header=False)
            s += f'{description}\n\n'
        if num_lines > 0 and not self.get_is_binary():
            s += self.get_file_header(num_lines)
        return s


class DataFileDescriptions(List[DataFileDescription]):
    """
    A list of data file descriptions.
    """

    def __init__(self, *args, data_folder: Optional[Union[str, Path]] = None,
                 general_description: Optional[Union[str, ReferencableTextProduct]] = None,
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
            self, data_file: DataFileDescription, index: Mutable = None, view_purpose: ViewPurpose = None):
        """
        Return a pretty description for the given data file and all its children.
        """
        children = self.get_children(data_file)
        index.val += 1
        s = data_file.pretty_repr(0 if children else 4, view_purpose=view_purpose, file_num=index.val) + '\n'
        for child in children:
            s += self.get_pretty_description_for_file_and_children(child, index)
        return s

    def pretty_repr(self, num_lines: int = 4, view_purpose: ViewPurpose = None) -> str:
        s = ''
        if self.general_description is not None:
            s += '## General Description\n'
            s += hypertarget_if_referencable_text_product(self.general_description, view_purpose,
                                                          with_header=False) + '\n'
        with run_in_directory(self.data_folder):
            s += '## Data Files\n'
            if len(self) == 0:
                s += 'There are no data files'
            elif len(self) == 1:
                s += f"The dataset consists of 1 data file:\n\n"
                s += self[0].pretty_repr(num_lines, view_purpose=view_purpose)
            else:
                s += f"The dataset consists of {len(self)} data files:\n\n"
                index = Mutable(0)
                for parent in self.get_all_raw_files():
                    s += self.get_pretty_description_for_file_and_children(parent, index, view_purpose=view_purpose)
            return s

    def get_data_filenames(self):
        return [data_file_description.file_path for data_file_description in self]

    def to_latex(self,
                 section_name: str = 'Data Description',
                 label: str = 'sec:data_description',
                 text: str = 'Here is the data description, as provided by the user:',
                 view_purpose: ViewPurpose = None) -> str:
        s = ''
        s += f"\\section{{{section_name}}} \\label{{{label}}} {text}"
        s += '\n\n' + wrap_as_latex_code_output(
            self.pretty_repr(num_lines=0, view_purpose=view_purpose))
        return s


@dataclass
class CreateDataFileDescriptions:
    """
    Given a project directory, create a temp folder to run in, and
    the data file descriptions.
    """
    project_directory: Path = None
    data_files_str_paths: List[str] = field(default_factory=list)
    data_files_is_binary: List[Optional[bool]] = field(default_factory=list)

    GENERAL_DESCRIPTION_FILENAME = 'general_description.txt'
    DESCRIPTION_FILENAME_EXT = '.description.txt'

    GENERAL_FILE_DESCRIPTION_PREFIX = 'S'
    FILE_DESCRIPTIONS_PREFIXES = ('T', 'U', 'V', 'W', 'X', 'Y', 'Z')

    temp_folder_to_run_in: Path = FOLDER_FOR_RUN

    def _get_description_file_path(self, data_file_path_str: str):
        data_file_path = self._convert_data_file_path_str_to_path(data_file_path_str)
        return self.project_directory / (data_file_path.name + self.DESCRIPTION_FILENAME_EXT)

    def _read_file_description(self, data_file_path_str: str):
        description_file_path = self._get_description_file_path(data_file_path_str)
        if not description_file_path.exists():
            raise FileNotFoundError(f"Description file for {data_file_path_str} not found.")
        return description_file_path.read_text()

    def _read_general_description(self):
        general_description_file_path = self.project_directory / self.GENERAL_DESCRIPTION_FILENAME
        if not general_description_file_path.exists():
            raise FileNotFoundError(f"General description file not found:\n{general_description_file_path}.")
        return general_description_file_path.read_text()

    def _get_hypertarget_prefix(self, file_num: Optional[int] = None, file_name: str = None):
        """
        Return the hypertarget prefix for the given file number.
        file_num: the file number. None refers to the general description.
        """
        return self.GENERAL_FILE_DESCRIPTION_PREFIX if file_num is None \
            else self.FILE_DESCRIPTIONS_PREFIXES[file_num]

    def _convert_description_to_referenceable_text(self, description: str, file_num: Optional[int],
                                                   file_name: str = None):
        """
        file_num: the file number. None refers to the general description.
        """
        return ReferencableTextProduct(
            referencable_text=NumericReferenceableText(
                text=description,
                hypertarget_prefix=self._get_hypertarget_prefix(file_num, file_name)),
            name=file_name,
        )

    def _convert_data_file_path_str_to_path(self, data_file_path: str):
        """
        convert to absolute path.
        if relative path, it is relative to the project directory.
        """
        return Path(data_file_path).absolute() if Path(data_file_path).is_absolute() \
            else self.project_directory / data_file_path

    def _get_file_description_referenceable_text(self, data_file_str_path: str, file_num: Optional[int]):
        description = self._read_file_description(data_file_str_path)
        data_file_path = self._convert_data_file_path_str_to_path(data_file_str_path)
        return self._convert_description_to_referenceable_text(description, file_num, data_file_path.name)

    def _get_general_description_referenceable_text(self):
        return self._convert_description_to_referenceable_text(self._read_general_description(), None,
                                                               'General Description')

    def _copy_files_and_get_list_of_data_file_descriptions(self) -> List[DataFileDescription]:
        data_file_descriptions = []
        clear_directory(self.temp_folder_to_run_in)  # clear data folder
        for j, data_file_str_path in enumerate(self.data_files_str_paths):
            data_file_path = self._convert_data_file_path_str_to_path(data_file_str_path)
            data_file_path_zip = data_file_path.with_name(data_file_path.name + '.zip')
            if os.path.exists(data_file_path):
                # copy file to data folder
                shutil.copyfile(data_file_path, self.temp_folder_to_run_in / data_file_path.name)
            elif os.path.exists(data_file_path_zip):
                # unzip file to data folder
                with zipfile.ZipFile(data_file_path_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.temp_folder_to_run_in)
            else:
                raise FileNotFoundError(f"File {data_file_path.name} or {data_file_path.name}.zip "
                                        f"not found in {data_file_path.parent}")

            data_file_descriptions.append(DataFileDescription(
                file_path=data_file_path.name,  # relative to data dir
                description=self._get_file_description_referenceable_text(data_file_str_path, j),
                is_binary=self.data_files_is_binary[j]
            ))
        return data_file_descriptions

    def create_temp_folder_and_get_file_descriptions(self) -> DataFileDescriptions:
        file_descriptions = self._copy_files_and_get_list_of_data_file_descriptions()
        return DataFileDescriptions(
            file_descriptions,
            data_folder=self.temp_folder_to_run_in,
            general_description=self._get_general_description_referenceable_text()
        )

    def get_raw_str_data_file_descriptions(self) -> DataFileDescriptions:
        return DataFileDescriptions(
            [DataFileDescription(
                file_path=data_file_str_path,  # relative to data dir
                description=self._read_file_description(data_file_str_path),
                is_binary=self.data_files_is_binary[j]
            ) for j, data_file_str_path in enumerate(self.data_files_str_paths)],
            data_folder=None,
            general_description=self._read_general_description(),
        )

    def create_file_descriptions(self, general_description: str, data_file_descriptions: List[str]):
        """
        Create the file descriptions.
        """
        (self.project_directory / self.GENERAL_DESCRIPTION_FILENAME).write_text(general_description)
        for j, data_file_str_path in enumerate(self.data_files_str_paths):
            self._get_description_file_path(data_file_str_path).write_text(data_file_descriptions[j])

    def check_files_exist(self):
        for data_file_str_path in self.data_files_str_paths:
            data_file_path = self._convert_data_file_path_str_to_path(data_file_str_path)
            data_file_path_zip = data_file_path.with_name(data_file_path.name + '.zip')
            if not data_file_path.exists() and not data_file_path_zip.exists():
                raise FileNotFoundError(f"Data file {data_file_path} not found.")
