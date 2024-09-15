import pickle

from data_to_paper.utils.file_utils import run_in_temp_directory


def simulate_save_load(func, obj, filename, *args, **kwargs):
    """
    Assume that func creates a pkl file filename.pkl
    Run the func. Read and return the pkl content.
    """
    with run_in_temp_directory():
        func(obj, filename, *args, **kwargs)
        with open(filename + '.pkl', 'rb') as f:
            return pickle.load(f)
