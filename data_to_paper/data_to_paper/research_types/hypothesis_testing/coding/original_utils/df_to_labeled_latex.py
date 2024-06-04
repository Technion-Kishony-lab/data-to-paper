from data_to_paper.code_and_output_files.referencable_text import label_numeric_value
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods import STR_FLOAT_FORMAT
from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_latex_with_value_format
from data_to_paper.run_gpt_code.overrides.pvalue import is_p_value, format_p_value, OnStr, OnStrPValue


def _format_obj(p_value):
    if is_p_value:
        s = format_p_value(p_value.value, smaller_than_sign='$<$')
        if s.startswith('$<$'):
            return '$<$' + label_numeric_value(s[3:])
        return label_numeric_value(s)


def df_to_numerically_labeled_latex(df, pvalue_on_str=OnStr.LATEX_SMALLER_THAN):
    """
    Get latex representation of a DataFrame with numeric values labeled.
    Label the numeric values with @@<...>@@ - to allow converting to ReferenceableText.
    """
    with OnStrPValue(pvalue_on_str):
        return to_latex_with_value_format(
            df, numeric_formater=lambda x: label_numeric_value(STR_FLOAT_FORMAT(x)),
            object_formatter=_format_obj)
