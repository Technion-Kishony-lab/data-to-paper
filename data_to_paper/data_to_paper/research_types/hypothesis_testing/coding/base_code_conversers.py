from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Optional, Dict

from data_to_paper.base_steps import BaseCodeProductsGPT
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.model_engines import get_model_engine_for_class
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts, get_code_name, \
    get_code_agent
from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import ScipyPValueOverride
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList


@dataclass
class BaseScientificCodeProductsHandler:
    code_step: str = ''  # "data_analysis", "data_exploration", "data_processing"
    products: ScientificProducts = None
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = None

    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    code_name: str = None
    conversation_name: str = None

    def __post_init__(self):
        if self.code_name is None:
            self.code_name = get_code_name(self.code_step)
        if self.conversation_name is None:
            self.conversation_name = f'{self.code_name} Code'
        if self.user_agent is None:
            self.user_agent = get_code_agent(self.code_step)


@dataclass
class BaseScientificCodeProductsGPT(BaseScientificCodeProductsHandler, BaseCodeProductsGPT):
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )  # None for the raw data files, () for no data files
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', 'research_goal')

    def __post_init__(self):
        BaseScientificCodeProductsHandler.__post_init__(self)
        BaseCodeProductsGPT.__post_init__(self)

    @property
    def files_created_in_prior_stages(self) -> NiceList[str]:
        files = NiceList([], wrap_with='"', separator='\n')
        for section in self.allow_data_files_from_sections:
            if section is None:
                continue
            if section in self.products.codes_and_outputs:
                files += self.products.codes_and_outputs[section].created_files.get_created_data_files()
        return files

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.raw_data_filenames + self.files_created_in_prior_stages,
                        wrap_with='"', prefix='\n', separator='\n', suffix='\n')

    @property
    def list_additional_data_files_if_any(self) -> str:
        if len(self.files_created_in_prior_stages) == 0:
            return ''
        return f'\nOr you can also use the processed files created above by the data processing code:\n' \
               f'```\n' \
               f'{self.files_created_in_prior_stages}' \
               f'```\n' \
               f'Important: use the correct version of the data to perform each of the steps. For example, ' \
               f'for descriptive statistics use the original data, for model building use the processed data.'

    @property
    def raw_data_filenames(self) -> NiceList[str]:
        if None in self.allow_data_files_from_sections:
            return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                            wrap_with='"',
                            prefix='{} data file[s]: ')
        return NiceList([], wrap_with='"', prefix='No data files.')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)


@dataclass
class BaseCreateTablesCodeProductsGPT(BaseScientificCodeProductsGPT):
    max_debug_iterations_per_attempt: int = 20
    max_code_revisions: int = 3
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(BaseCreateTablesCodeProductsGPT))
    user_agent: ScientificAgent = ScientificAgent.Debugger
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn')

    @staticmethod
    def _get_regression_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'statsmodels' not in code_and_output.code:
            return ''
        linear_regression_funcs = ['ols(', 'OLS(', 'logit(', 'Logit(', 'glm(', 'GLM(']
        code = code_and_output.code
        func_names = [func for func in linear_regression_funcs if func in code]
        if not func_names:
            return ''
        return dedent_triple_quote_str("""\n
            # - In regressions, in case interactions terms are included:
            # Is the main effect adequately included in the model with interaction terms?
            # Did we use the `*` operator in statsmodels formula as recommended?
            # (as applicable, better use `formula = "y ~ a * b"`, instead of trying to \t
            manually multiply the variables)
            # For example:
            "Model with interaction terms": 
                ("CONCERN", "We forgot to include the main effect in the xxx model, \t
            please use the `*` operator in the formula")
            """, indent=4)

    @staticmethod
    def _get_mediation_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'mediation' not in code_and_output.code.lower() and False:
            return ''
        return dedent_triple_quote_str("""\n
            # - In mediation analysis:
            # did we calculate the mediation effect (e.g., using the Sobel test or other)?
            # did we account for relevant confounding factors?
            # (by adding these same confounding factors to both the 'a' and 'b' paths)
            # For example:
            "Mediation analysis":
                ("CONCERN", "We did not explicitly calculate the mediation effect")
            """, indent=4)

    @staticmethod
    def _get_machine_learning_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'sklearn' not in code_and_output.code:
            return ''
        ml_funcs = ['RandomForestClassifier(', 'RandomForestRegressor(',
                    'ElasticNet(', 'SVR(', 'SVC(', 'MLPRegressor(',
                    'DecisionTreeClassifier(',
                    'DecisionTreeRegressor(', 'LogisticRegression(']
        func_names = [func for func in ml_funcs if func in code_and_output.code]
        if not func_names:
            return ''
        return dedent_triple_quote_str("""\n
            # - Machine-Learning models:
            # Are we adequately performing hyperparameter tuning using cross-validation (as appropriate). 
            # Are the best hyperparameters reported (either in a table file or in the "additional_results.pkl" file).
            # For example:
            "Hyperparameter tuning":
                ("CONCERN", "We forgot to perform hyperparameter tuning")
            """, indent=4)

    @staticmethod
    def _get_scipy_unpacking_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        override_stats = code_and_output.contexts['OverrideStatisticsPackages']
        assert isinstance(override_stats, OverrideStatisticsPackages)
        stat_contexts = override_stats.contexts
        scipy_context = next((context for context in stat_contexts if isinstance(context, ScipyPValueOverride)), None)
        if scipy_context:
            func_to_fields = scipy_context.unpacking_func_to_fields
            if func_to_fields:
                s = ('\n# - Unpacking order\n'
                     '# When unpacking or indexing the results of {}, are we using the correct order of fields?\n'). \
                    format(NiceList(func_to_fields.keys(), wrap_with="`", last_separator=" or "))
                for func, fields in func_to_fields.items():
                    s += f'#   The correct order for `{func}` is: {NiceList(fields, wrap_with="`")}.\n'
                return s
        return ''

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        comments = super()._get_specific_attrs_for_code_and_output(code_and_output)
        comments['regression_comments'] = self._get_regression_comments_for_code_and_output(code_and_output)
        comments['mediation_comments'] = self._get_mediation_comments_for_code_and_output(code_and_output)
        comments['machine_learning_comments'] = self._get_machine_learning_comments_for_code_and_output(code_and_output)
        comments['scipy_unpacking_comments'] = self._get_scipy_unpacking_comments_for_code_and_output(code_and_output)
        return comments
