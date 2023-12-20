import functools
from dataclasses import dataclass

from data_to_paper.env import TRACK_P_VALUES
from ..attr_replacers import SystematicMethodReplacerContext, SystematicFuncReplacerContext
from ..types import convert_to_p_value, PValue
from ...types import RunIssue, RunUtilsError, CodeProblem


MULTITEST_FUNCS_AND_PVAL_INDEXES = [
    ('multipletests', 1),
    ('fdrcorrection_twostage', 1),
    ('fdrcorrection', 1),
]


ANOVA_FUNCS = [
    'anova_single',
    'anova1_lm_single',
    'anova2_lm_single',
    'anova3_lm_single',
    'anova_lm',
]


def _get_summary2_func(self, original_func):
    """
    Get the overridden summary2 function of a statsmodels class.
    """

    def custom_summary2(*args, **kwargs):
        """
        A custom summary2 function that replaces the pvalues attribute of the summary tables with a PValue objects.
        Replaces "P>|t|" and "P>|z|" with PValue objects.
        """
        with PValue.allow_str.temporary_set(True):
            result = original_func(self, *args, **kwargs)

        tables = result.tables
        table1 = tables[1]

        pval_names = [name for name in table1.columns if name.startswith('P>')]
        for pval_name in pval_names:
            table1[pval_name] = convert_to_p_value(table1[pval_name], created_by=self.__class__.__name__)
        return result

    return custom_summary2


def _get_summary_func(self, original_func):
    """
    Get the overridden summary function of a statsmodels class.
    """

    def custom_summary(*args, **kwargs):
        """
        Prevents the use of the summary function.
        """
        raise RunUtilsError(RunIssue(
            issue=f"Do not use the `summary` function of statsmodels.",
            instructions=f"Use the `summary2` function instead.",
            code_problem=CodeProblem.RuntimeError,
        ))

    return custom_summary


@dataclass
class StatsmodelsFitPValueOverride(SystematicMethodReplacerContext):
    """
    A context manager that replaces the pvalues attribute of all fit functions in statsmodels with a
    PValue.
    """
    obj_import_str: str = 'statsmodels'

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return attr_name.startswith('fit')

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            result = original_func(obj, *args, **kwargs)
            if self._is_called_from_data_to_paper():
                if hasattr(obj, '_prior_fit_results') and obj._prior_fit_results is result:
                    raise RuntimeWarning(
                        f"The `{original_func.__name__}` function was already called on this object. "
                        f"Multiple calls should be avoided as the same result instance is returned again.")
                obj._prior_fit_results = result

            if TRACK_P_VALUES:
                # Replace the pvalues attribute if it exists
                # result.pvalues = result.pvalues.astype(PValueDtype(self.__class__.__name__))
                for attr in ['pvalues', 'f_pvalue', 'pvalue']:
                    if not hasattr(result, attr):
                        continue
                    pvalues = getattr(result, attr)
                    pvalues = convert_to_p_value(pvalues, created_by=obj.__class__.__name__,
                                                 raise_on_nan=attr != 'f_pvalue')
                    try:
                        setattr(result, attr, pvalues)
                    except AttributeError:
                        if attr in getattr(result, '_cache', {}):
                            result._cache[attr] = pvalues

                if hasattr(result, 'summary2'):
                    original_summary2 = result.summary2
                    result.summary2 = _get_summary2_func(obj, original_summary2)

                if hasattr(result, 'summary'):
                    original_summary = result.summary
                    result.summary = _get_summary_func(obj, original_summary)
            return result

        return wrapped


@dataclass
class StatsmodelsMultitestPValueOverride(SystematicFuncReplacerContext):
    obj_import_str: str = 'statsmodels.stats.multitest'

    def _should_replace(self, module, func_name, func) -> bool:
        return func_name in [func_name for func_name, _ in MULTITEST_FUNCS_AND_PVAL_INDEXES]

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(*args, **kwargs):
            result = original_func(*args, **kwargs)

            if TRACK_P_VALUES:
                # Replace the pvalues attribute if it exists
                try:
                    func_name, pval_index = [x for x in MULTITEST_FUNCS_AND_PVAL_INDEXES if x[0] == attr_name][0]
                    result = list(result)
                    result[pval_index] = convert_to_p_value(result[pval_index], created_by=func_name)
                    result = tuple(result)
                except (AttributeError, TypeError, ValueError):
                    pass
            return result

        return wrapped


@dataclass
class StatsmodelsAnovaPValueOverride(SystematicFuncReplacerContext):
    obj_import_str: str = 'statsmodels.stats.anova'

    def _should_replace(self, module, func_name, func) -> bool:
        return func_name in ANOVA_FUNCS

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(*args, **kwargs):
            result = original_func(*args, **kwargs)

            if TRACK_P_VALUES:
                # Replace the 'PR(>F)' column with PValue objects
                try:
                    for row_label in result.index:
                        result.loc[row_label, 'PR(>F)'] = convert_to_p_value(result.loc[row_label, 'PR(>F)'],
                                                                             created_by=attr_name,
                                                                             raise_on_nan=row_label != 'Residual')
                except (AttributeError, TypeError, ValueError):
                    pass
            return result

        return wrapped
