from typing import Optional, Tuple

THEME_NAME = 'big_bang_theory'


MAX_BARS: int = 50


KIND_TO_MAX_ROWS_AND_COLUMNS_FOR_PLOT = {
    None: (50, 10),  # Default
    'bar': (50, 10),
    'hist': (None, 10),
}


KIND_TO_MAX_ROWS_AND_COLUMNS_FOR_SHOW = {
    None: (50, 10),  # Default
    'bar': (50, 10),
    'hist': (5, 10),
}


TABLE_MAX_ROWS_AND_COLUMNS: Tuple[Optional[int], Optional[int]] = (20, 6)


def get_max_rows_and_columns(is_figure: bool, kind: Optional[str], to_show: bool = False
                             ) -> tuple[Optional[int], Optional[int]]:
    if not is_figure:
        return TABLE_MAX_ROWS_AND_COLUMNS
    dict_ = KIND_TO_MAX_ROWS_AND_COLUMNS_FOR_SHOW if to_show else KIND_TO_MAX_ROWS_AND_COLUMNS_FOR_PLOT
    return dict_.get(kind, dict_[None])
