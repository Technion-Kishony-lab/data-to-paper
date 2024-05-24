from __future__ import annotations
import functools
from typing import Iterable, Callable
from dataclasses import dataclass

from data_to_paper.env import TRACK_P_VALUES
from ...attr_replacers import SystematicMethodReplacerContext, SystematicFuncReplacerContext, AttrReplacer
from ...run_issues import CodeProblem, RunIssue
from ..pvalue import convert_to_p_value, PValue, TrackPValueCreationFuncs

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


@dataclass
class StatsmodelsFitPValueOverride(SystematicMethodReplacerContext, TrackPValueCreationFuncs):
    """
    A context manager that replaces the pvalues attribute of all fit functions in statsmodels with a
    PValue.
    """
    package_names: Iterable[str] = ('statsmodels', )

    def _get_all_modules(self) -> list:
        from statsmodels.regression import linear_model
        from statsmodels.genmod import generalized_linear_model
        from statsmodels.discrete import discrete_model
        return [linear_model, generalized_linear_model, discrete_model]

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return attr_name.startswith('fit')

    def _get_summary2_func(self, obj, original_func: Callable, created_by: str):
        """
        Get the overridden summary2 function of a statsmodels class.
        """

        def custom_summary2(*args, **kwargs):
            """
            A custom summary2 function that replaces the pvalues attribute of the summary tables with a PValue objects.
            Replaces "P>|t|" and "P>|z|" with PValue objects.
            """
            with PValue.BEHAVE_NORMALLY.temporary_set(True):
                result = original_func(obj, *args, **kwargs)

            tables = result.tables
            table1 = tables[1]

            pval_names = [name for name in table1.columns if name.startswith('P>')]
            for pval_name in pval_names:
                table1[pval_name] = convert_to_p_value(table1[pval_name], created_by=created_by, var_name=pval_name,
                                                       context=self)

            return result

        return custom_summary2

    def _get_summary_func(self, obj, original_func):
        """
        Get the overridden summary function of a statsmodels class.
        """

        def custom_summary(*args, **kwargs):
            """
            Prevents the use of the summary function.
            """
            raise RunIssue.from_current_tb(
                category="Statsmodels: good practices",
                issue=f"Do not use the `summary` function of statsmodels.",
                instructions=f"Use the `summary2` function instead.",
                code_problem=CodeProblem.RuntimeError,
            )

        return custom_summary

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            result = original_func(obj, *args, **kwargs)
            if self._is_called_from_data_to_paper():
                if hasattr(obj, '_prior_fit_results') and obj._prior_fit_results is result:
                    raise RunIssue.from_current_tb(
                        category='Statsmodels: good practices',
                        issue=f"The `{original_func.__name__}` function was already called on this object. ",
                        instructions=f"Multiple calls should be avoided as the same result instance is returned again.",
                        code_problem=CodeProblem.RuntimeError,
                    )
                obj._prior_fit_results = result

            if TRACK_P_VALUES:
                # Replace the pvalues attribute if it exists
                created_by = obj.__class__.__name__
                pvalue_detected = False
                for attr in ['pvalues', 'f_pvalue', 'pvalue']:
                    if not hasattr(result, attr):
                        continue
                    pvalues = getattr(result, attr)
                    pvalues = convert_to_p_value(pvalues, created_by=created_by, context=self,
                                                 raise_on_nan=attr != 'f_pvalue')
                    pvalue_detected = True
                    try:
                        setattr(result, attr, pvalues)
                    except AttributeError:
                        if attr in getattr(result, '_cache', {}):
                            result._cache[attr] = pvalues

                if hasattr(result, 'summary2'):
                    original_summary2 = result.summary2
                    result.summary2 = self._get_summary2_func(obj, original_summary2, created_by)
                    pvalue_detected = True

                if hasattr(result, 'summary'):
                    original_summary = result.summary
                    result.summary = self._get_summary_func(obj, original_summary)
                    pvalue_detected = True

                if hasattr(result, 'eigenvals'):
                    eigenvals = result.eigenvals
                    if eigenvals is not None:
                        min_eigenval = eigenvals[-1]
                        assert min_eigenval == min(eigenvals)
                        if min_eigenval < 1e-10:
                            self.issues.append(RunIssue.from_current_tb(
                                category='Statsmodels: eigenvalues too small',
                                issue="The eigenvalues of the covariance matrix are too small. "
                                      "This might indicate that there are strong multicollinearity problems "
                                      "or that the design matrix is singular.",
                                instructions="Try to remove redundant features.",
                                code_problem=CodeProblem.RuntimeError,
                            ))

                if pvalue_detected:
                    self._add_pvalue_creating_func(created_by)
            return result

        return wrapped


@dataclass
class StatsmodelsMultitestPValueOverride(SystematicFuncReplacerContext, TrackPValueCreationFuncs):
    package_names: Iterable[str] = ('statsmodels', )
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
                    result[pval_index] = convert_to_p_value(result[pval_index], created_by=func_name, context=self)
                    result = tuple(result)
                    self._add_pvalue_creating_func(func_name)
                except (AttributeError, TypeError, ValueError):
                    pass
            return result

        return wrapped


@dataclass
class StatsmodelsAnovaPValueOverride(SystematicFuncReplacerContext, TrackPValueCreationFuncs):
    package_names: Iterable[str] = ('statsmodels', )
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
                                                                             var_name=row_label,
                                                                             raise_on_nan=row_label != 'Residual',
                                                                             context=self)
                    self._add_pvalue_creating_func(attr_name)
                except (AttributeError, TypeError, ValueError):
                    pass
            return result

        return wrapped


@dataclass
class StatsmodelsMulticompPValueOverride(AttrReplacer, TrackPValueCreationFuncs):
    package_names: Iterable[str] = ('statsmodels', )
    obj_import_str: str = 'statsmodels.sandbox.stats.multicomp.TukeyHSDResults'
    attr: str = '__init__'

    def _is_called_from_data_to_paper(self, offset: int = 3) -> bool:
        return True

    def _get_wrapped_wrapper(self):

        def TukeyHSDResults__init__(obj, mc_object, results_table, q_crit, reject=None,
                                    meandiffs=None, std_pairs=None, confint=None, df_total=None,
                                    reject2=None, variance=None, pvalues=None):
            """
            A custom __init__ function for TukeyHSDResults that replaces the pvalues attribute with a PValue object.
            """
            pvalues = convert_to_p_value(pvalues, created_by='TukeyHSDResults')

            p_adj_index = 3
            for row in results_table[1:]:
                row[p_adj_index].data = convert_to_p_value(row[p_adj_index].data, created_by='TukeyHSDResults',
                                                           var_name=row[0].data, context=self)

            self._add_pvalue_creating_func('TukeyHSDResults')
            return self._original(obj, mc_object, results_table, q_crit, reject=reject,
                                  meandiffs=meandiffs, std_pairs=std_pairs, confint=confint, df_total=df_total,
                                  reject2=reject2, variance=variance, pvalues=pvalues)

        return TukeyHSDResults__init__
