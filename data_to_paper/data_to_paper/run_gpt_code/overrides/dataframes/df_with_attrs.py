import pandas as pd


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


class ListInfoDataFrame(InfoDataFrame):

    @classmethod
    def from_prior_df(cls, df, extra_info=None):
        if isinstance(df, cls):
            prior_extra_info = df.extra_info
        else:
            prior_extra_info = []
        return cls(df, extra_info=prior_extra_info + [extra_info])


def save_as_list_info_df(func_name, df, filename, kwargs=None):
    """
    save df to pickle with the func
    """
    kwargs = {} if kwargs is None else kwargs
    df = ListInfoDataFrame.from_prior_df(df, (func_name, df, filename, kwargs))
    pickle_filename = filename + '.pkl'
    df.to_pickle(pickle_filename)
