from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Union, Tuple, Dict, Callable, NamedTuple

from scientistgpt.conversation.stage import Stage
from scientistgpt.utils.file_utils import run_in_directory
from scientistgpt.utils.mutable import Mutable
from scientistgpt.utils.text_formatting import format_with_args_or_kwargs, ArgsOrKwargs


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: str  # a user provided description of the file
    originated_from: Optional[str] = None  # None for raw file

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file.
        """
        with open(self.file_path) as f:
            # Note: DO NOT do ''.join(f.readlines()[:num_lines]) because that will read the whole file
            head = [next(f) for _ in range(num_lines)]
            return ''.join(head)

    def pretty_repr(self, num_lines: int = 4):
        s = f'"{self.file_path}"\n{self.description}\n\n'
        if num_lines > 0:
            s += f'Here are the first few lines of the file:\n' \
                 f'```\n{self.get_file_header(num_lines)}\n```\n'
        return s


class DataFileDescriptions(List[DataFileDescription]):
    """
    A list of data file descriptions.
    """

    def __init__(self, *args, data_folder: Optional[Union[str, Path]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_folder = data_folder

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
        with run_in_directory(self.data_folder):
            if len(self) == 0:
                s = 'No data files'
            elif len(self) == 1:
                s = "1 data file:\n\n"
                s += self[0].pretty_repr(num_lines)
            else:
                s = f"{len(self)} data files:\n"
                index = Mutable(0)
                for parent in self.get_all_raw_files():
                    s += self.get_pretty_description_for_file_and_children(parent, index)
            return s

    def get_data_filenames(self):
        return [data_file_description.file_path for data_file_description in self]


class NameDescriptionStage(NamedTuple):
    name: str
    description: str
    stage: Stage


class NameDescriptionStageGenerator(NamedTuple):
    name: str
    description: str
    stage: Union[Stage, Callable]
    func: Callable


def _convert_args_or_kwargs_to_args(args_or_kwargs: ArgsOrKwargs) -> Tuple[str]:
    """
    Convert the given args or kwargs to args.
    """
    if isinstance(args_or_kwargs, tuple):
        return args_or_kwargs
    else:
        return tuple(args_or_kwargs.values())


@dataclass
class Products:
    """
    Contains the different outcomes of the process.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """

    _fields_to_name_description_stage: Dict[str, NameDescriptionStageGenerator] = None
    _raise_on_none: bool = False

    def __post_init__(self):
        self._fields_to_name_description_stage = self._get_generators()

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        """
        Return a dictionary mapping product fields to a tuple of
        (name: str, description: str, stage: Stages, func: Callable).
        func is a function that creates args for the name and description to be formatted with.
        """
        return {}

    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        return self._get_name_description_stage(product_field).name

    def get_description(self, product_field: str) -> str:
        """
        Return the description of the given product.
        """
        return self._get_name_description_stage(product_field).description

    def get_stage(self, product_field: str) -> Stage:
        """
        Return the stage of the given product.
        """
        return self._get_name_description_stage(product_field).stage

    @staticmethod
    def extract_subfields(field: str) -> List[str]:
        """
        Return a list of subfields of the given field.
        """
        return field.split(':')

    def _get_name_description_stage_generators_and_variables(self, field: str
                                                             ) -> Tuple[NameDescriptionStage, ArgsOrKwargs]:
        """
        Return the name, stage, and description variables of the given field.
        """
        (name, description, stage, func), args = self._get_name_stage_description_generator_and_args(field)
        variables = func(*args)
        if not isinstance(stage, Stage):
            stage = stage(*args)
        if not isinstance(variables, (tuple, dict)):
            variables = (variables, )
        return NameDescriptionStage(name, description, stage), variables

    def _get_name_description_stage(self, field: str) -> NameDescriptionStage:
        """
        Return the name, stage, and description generator of the given field.
        """
        (name, description, stage), variables = self._get_name_description_stage_generators_and_variables(field)
        if self._raise_on_none and any(v is None for v in _convert_args_or_kwargs_to_args(variables)):
            raise ValueError(f'One of the variables in {variables} is None')
        name = format_with_args_or_kwargs(name, variables)
        description = format_with_args_or_kwargs(description, variables)
        return NameDescriptionStage(name, description, stage)

    def _get_name_stage_description_generator_and_args(self, field: str
                                                       ) -> Tuple[NameDescriptionStageGenerator, List[str]]:
        """
        Return the name, stage, and description of the given field.
        """
        subfields = self.extract_subfields(field)
        for current_field, name_stage_description in self._fields_to_name_description_stage.items():
            current_subfields = self.extract_subfields(current_field)
            wildcard_subfields = []
            if len(subfields) == len(current_subfields):
                for subfield, current_subfield in zip(subfields, current_subfields):
                    if current_subfield == '{}':
                        wildcard_subfields.append(subfield)
                    elif subfield != current_subfield:
                        break
                else:
                    return name_stage_description, wildcard_subfields
        raise ValueError(f'Unknown product field: {field}')

    def is_product_available(self, field: str) -> bool:
        """
        Return whether the given product is available.
        """
        try:
            self._raise_on_none = True
            _, variables = self._get_name_description_stage_generators_and_variables(field)
            variables = _convert_args_or_kwargs_to_args(variables)
            return variables[0] is not None
        except (KeyError, AttributeError, ValueError):
            return False
        finally:
            self._raise_on_none = False

    def __getitem__(self, item) -> NameDescriptionStage:
        return self._get_name_description_stage(item)
