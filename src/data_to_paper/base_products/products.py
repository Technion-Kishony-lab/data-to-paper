from dataclasses import dataclass
from typing import NamedTuple, Union, Callable, Tuple, Dict, List, Any

from data_to_paper.base_products.product import Product
from data_to_paper.conversation.stage import Stage
from data_to_paper.text.highlighted_text import format_text_with_code_blocks
from data_to_paper.text.text_formatting import ArgsOrKwargs, format_with_args_or_kwargs


class NameDescriptionStage(NamedTuple):
    name: str
    description: str
    stage: Stage


class NameDescriptionStageGenerator(NamedTuple):
    name: str
    description: str
    stage: Union[Stage, Callable]
    func: Callable


class ProductGenerator(NamedTuple):
    product: Union[Product, Callable]
    kwargs: Union[Dict[str, Any], Callable]


UnifiedProduct = Union[NameDescriptionStage, Product]
UnifiedProductGenerator = Union[NameDescriptionStageGenerator, ProductGenerator]


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
    These outcomes are gradually populated, where in each stage we get a new product based on previous products
    from prior stages.
    """

    _fields_to_unified_product_generators: Dict[str, UnifiedProductGenerator] = None
    _raise_on_none: bool = False

    def __post_init__(self):
        self._fields_to_unified_product_generators = self._get_generators()

    def _get_generators(self) -> Dict[str, UnifiedProductGenerator]:
        """
        Return a dictionary mapping product fields to a tuple of
        (name: str, description: str, stage: Stage, func: Callable).
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

    def _get_unified_product_and_variables(self, field: str
                                           ) -> Tuple[UnifiedProduct, ArgsOrKwargs]:
        """
        Return the name, stage, and description variables of the given field.
        """
        unified_product_generator, args = self._get_unified_product_generator_and_args(field)
        if isinstance(unified_product_generator, NameDescriptionStageGenerator):
            name, description, stage, func = unified_product_generator
            variables = func(*args)
            if not isinstance(stage, Stage):
                stage = stage(*args)
            if not isinstance(variables, (tuple, dict)):
                variables = (variables, )
            return NameDescriptionStage(name, description, stage), variables
        elif isinstance(unified_product_generator, ProductGenerator):
            product, kwargs = unified_product_generator
            if not isinstance(product, Product):
                product = product(*args)
            if not isinstance(product, Product):
                raise ValueError(f'Unknown product field: {field}')
            if not product.is_valid():
                raise ValueError(f'Product {product} is not valid')
            if not isinstance(kwargs, dict):
                kwargs = kwargs(*args)
            return product, kwargs
        else:
            raise ValueError(f'Unknown product field: {field}')

    def _get_name_description_stage(self, field: str) -> NameDescriptionStage:
        """
        Return the name, stage, and description generator of the given field.
        """
        unified_product, variables = self._get_unified_product_and_variables(field)
        if self._raise_on_none and any(v is None for v in _convert_args_or_kwargs_to_args(variables)):
            raise ValueError(f'One of the variables in {variables} is None')
        if isinstance(unified_product, NameDescriptionStage):
            name, description, stage = unified_product
            name = format_with_args_or_kwargs(name, variables)
            description = format_with_args_or_kwargs(description, variables)
            return NameDescriptionStage(name, description, stage)
        elif isinstance(unified_product, Product):
            format_name = variables.pop('format_name') \
                if 'format_name' in variables else 'markdown'
            level = variables.pop('level') if 'level' in variables else 2
            return NameDescriptionStage(
                unified_product.get_header(**variables),
                unified_product.as_formatted_text(with_header=False, **variables),
                unified_product.get_stage(format_name=format_name, level=level,
                                          **variables),
            )
        else:
            raise ValueError(f'Unknown product field: {field}')

    def get_description_as_html(self, field: str) -> str:
        """
        Return the product of the given field.
        """
        unified_product, variables = self._get_unified_product_and_variables(field)
        if isinstance(unified_product, Product):
            return unified_product.as_html(level=1, **variables)
        description = self.get_description(field)
        return ('<h1>' + self.get_name(field) + '</h1>\n' +
                format_text_with_code_blocks(description, is_html=True, width=None, from_md=True))

    def get_description_for_llm(self, field: str) -> str:
        """
        Return the product in a format to be used in conversation context for the LLM.
        """
        name = self.get_name(field)
        description = self.get_description(field)
        return f'# {name}\n{description}'

    def _get_unified_product_generator_and_args(self, field: str
                                                ) -> Tuple[UnifiedProductGenerator, List[str]]:
        """
        Return the name, stage, and description of the given field.
        """
        subfields = self.extract_subfields(field)
        for current_field, unified_product in self._fields_to_unified_product_generators.items():
            current_subfields = self.extract_subfields(current_field)
            wildcard_subfields = []
            if len(subfields) == len(current_subfields):
                for subfield, current_subfield in zip(subfields, current_subfields):
                    if current_subfield == '{}':
                        wildcard_subfields.append(subfield)
                    elif subfield != current_subfield:
                        break
                else:
                    return unified_product, wildcard_subfields
        raise ValueError(f'Unknown product field: {field}')

    def is_product_available(self, field: str) -> bool:
        """
        Return whether the given product field is available.
        A product field is available if all of its variables are not None and all of the sub-products it
        depends on are available (not None).
        Trying to access an unavailable attributes is also interpreted as False, namely the sub-product
        is not available.
        """
        try:
            self._raise_on_none = True
            _, variables = self._get_unified_product_and_variables(field)
            variables = _convert_args_or_kwargs_to_args(variables)
            return all(variable is not None for variable in variables)
        except (KeyError, AttributeError, ValueError):
            return False
        finally:
            self._raise_on_none = False

    def __getitem__(self, item) -> NameDescriptionStage:
        return self._get_name_description_stage(item)
