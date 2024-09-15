import pandas as pd

from typing import Any, Dict, NamedTuple, Tuple, Callable, Optional


class InfoDataFrame(pd.DataFrame):
    """
    Custom DataFrame class with additional extra_info attribute
    Allows for custom state handling during pickling saving and loading
    """
    _metadata = pd.DataFrame._metadata + ['extra_info']

    def __init__(self, *args, extra_info=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_info = extra_info

    # Ensure the custom constructor handles extra_info
    @property
    def _constructor(self):
        def _c(*args, **kwargs):
            cls = type(self)
            return cls(*args, extra_info=self.extra_info, **kwargs)

        return _c

    def __reduce__(self):
        pickled_state = super().__reduce__()
        # Custom state handling
        new_state = pickled_state[2].copy()
        new_state['extra_info'] = self.extra_info
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state):
        # Restore extra_info safely
        self.extra_info = state.pop('extra_info', None)
        super().__setstate__(state)

    def transpose(self, *args, **kwargs):
        # Ensure the custom constructor handles extra_info
        df = super().transpose(*args, **kwargs)
        df = self._constructor(df)
        return df


class FuncCallParams(NamedTuple):
    """
    Stores a func call.
    """
    func: Callable
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = {}

    def call(self, **extra_kwargs):
        return self.func(*self.args, **self.kwargs, **extra_kwargs)

    @property
    def func_name(self):
        return self.func.__name__


class SaveObjFuncCallParams(FuncCallParams):
    """
    Stores a func call that saves an obj to a file
    """
    @classmethod
    def from_(cls, func, obj, filename, *args, **kwargs):
        return cls(func=func, args=(obj, filename) + args, kwargs=kwargs)

    @property
    def obj(self):
        return self.args[0]

    @property
    def filename(self):
        return self.args[1]

    @property
    def extra_args(self):
        return self.args[2:]


class InfoDataFrameWithSaveObjFuncCall(InfoDataFrame):
    """
    Custom DataFrame class where extra_info is a FuncCallParams
    """
    def __init__(self, *args, extra_info: SaveObjFuncCallParams = None, **kwargs):
        super().__init__(*args, extra_info=extra_info, **kwargs)

    def get_func_call(self) -> SaveObjFuncCallParams:
        return self.extra_info

    def get_prior_filename(self) -> Optional[str]:
        prior_df = self.extra_info.obj
        if not isinstance(prior_df, InfoDataFrameWithSaveObjFuncCall):
            return None
        return prior_df.get_func_call().filename


def save_as_func_call_df(func, df, filename, kwargs=None) -> InfoDataFrameWithSaveObjFuncCall:
    """
    save df to pickle with the func
    """
    kwargs = kwargs if kwargs is not None else {}
    df = InfoDataFrameWithSaveObjFuncCall(df, extra_info=SaveObjFuncCallParams.from_(func, df, filename, **kwargs))
    if filename:
        pickle_filename = filename + '.pkl'
        df.to_pickle(pickle_filename)
    return df
