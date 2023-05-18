from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Union, Tuple, ClassVar, Dict

from scientistgpt.conversation.stage import Stage
from scientistgpt.utils.file_utils import run_in_directory
from scientistgpt.utils.text_utils import replace_text_by_dict, evaluate_string


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

    def pretty_repr(self, num_lines: int = 4):
        s = f'{self.file_path}\n{self.description}\n\n'
        if num_lines > 0:
            s += f'Here are the first few lines of the file:\n' \
                 f'```\n{self.get_file_header(num_lines)}\n```'
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

    def pretty_repr(self, num_lines: int = 4):
        with run_in_directory(self.data_folder):
            if len(self) == 0:
                s = 'No data files'
            elif len(self) == 1:
                s = "1 data file:\n\n"
                s += self[0].pretty_repr(num_lines)
            else:
                s = f"{len(self)} data files:\n"
                for file_number, data_file_description in enumerate(self):
                    s += f"\n({file_number + 1}) " + data_file_description.pretty_repr(num_lines)
            return s

    def get_data_filenames(self):
        return [data_file_description.file_path for data_file_description in self]


NameStageDescription = Tuple[str, Stage, str]


def get_subfield_variable(subfield: str) -> Optional[str]:
    if subfield.startswith('{') and subfield.endswith('}'):
        return subfield[1:-1]
    return None


@dataclass
class Products:
    """
    Contains the different outcomes of the process.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """

    FIELDS_TO_NAME_STAGE_DESCRIPTION: ClassVar[Dict[str, NameStageDescription]] = {}

    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        return self.get_evaluated_name_stage_description(product_field)[0]

    def get_stage(self, product_field: str) -> Stage:
        """
        Return the stage of the given product.
        """
        return self.get_evaluated_name_stage_description(product_field)[1]

    def get_description(self, product_field: str) -> str:
        """
        Return the description of the given product.
        """
        return self.get_evaluated_name_stage_description(product_field)[2]

    @staticmethod
    def extract_subfields(field: str) -> List[str]:
        """
        Return a list of subfields of the given field.
        """
        return field.split(':')

    def get_unformatted_name_stage_description(self, field: str) -> Tuple[NameStageDescription, Dict[str, str]]:
        """
        Return the name, stage, and description of the given field.
        """
        subfields = self.extract_subfields(field)
        for current_field, name_stage_description in self.FIELDS_TO_NAME_STAGE_DESCRIPTION.items():
            current_subfields = self.extract_subfields(current_field)
            variables_to_subfields = {}
            if len(subfields) == len(current_subfields):
                for subfield, current_subfield in zip(subfields, current_subfields):
                    current_subfield_variable = get_subfield_variable(current_subfield)
                    if current_subfield_variable:
                        variables_to_subfields[current_subfield_variable] = subfield
                    elif subfield != current_subfield:
                        break
                else:
                    return name_stage_description, variables_to_subfields
        raise ValueError(f'Unknown product field: {field}')

    def get_formatted_name_stage_description(self, field: str) -> NameStageDescription:
        """
        Return the name, stage, and description of the given field, formatted with the given variables.
        """
        (name, stage, description), variables_to_subfields = self.get_unformatted_name_stage_description(field)
        replacements = {'{' + var + '}': val for var, val in variables_to_subfields.items()}
        name = replace_text_by_dict(name, replacements)
        description = replace_text_by_dict(description, replacements)
        return name, stage, description

    def get_evaluated_name_stage_description(self, field: str) -> NameStageDescription:
        """
        Return the name, stage, and description of the given field, formatted with the given variables.
        """
        name, stage, description = self.get_formatted_name_stage_description(field)
        name = evaluate_string(name)
        description = evaluate_string(description)
        return name, stage, description

    def __getitem__(self, item):
        return self.get_evaluated_name_stage_description(item)
