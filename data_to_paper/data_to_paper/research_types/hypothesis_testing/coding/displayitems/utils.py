from data_to_paper.run_gpt_code.attr_replacers import AttrReplacer


def _read_pickle_and_save_filename(*args, original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Read a pickle file into a data frame.
    Save the filename.
    """
    filename = args[0] if args else kwargs.get('path', None)
    if filename:
        context_manager.last_read_pickle_filename = filename
    return original_func(*args, **kwargs)


def get_df_read_pickle_attr_replacer():
    context = AttrReplacer(obj_import_str='pandas', attr='read_pickle', wrapper=_read_pickle_and_save_filename,
                           send_context_to_wrapper=True, send_original_to_wrapper=True)
    context.last_read_pickle_filename = None
    return context

