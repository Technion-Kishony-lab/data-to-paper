import multiprocessing
import os
import pickle
import tempfile
import uuid


def process_func(queue, func, *args, **kwargs):
    exception = None
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        exception = e
        result = None
    result_exception = (result, exception)
    if isinstance(queue, str):
        with open(queue, 'wb') as f:
            pickle.dump(result_exception, f)
    else:
        queue.put(result_exception)


def run_func_in_separate_process(func, *args, in_separate_process=True,
                                 use_file_instead_of_queue=True,
                                 **kwargs):
    if not in_separate_process:
        return process_func(None, func, *args, **kwargs)
    if use_file_instead_of_queue:
        queue_or_filepath = f"subprocess_output_{uuid.uuid4()}_{os.getpid()}.pkl"
        queue_or_filepath = os.path.join(tempfile.gettempdir(), queue_or_filepath)
    else:
        queue_or_filepath = multiprocessing.Queue()
    process = multiprocessing.Process(target=process_func, args=(queue_or_filepath, func, *args), kwargs=kwargs)
    process.start()
    process.join()
    if use_file_instead_of_queue:
        with open(queue_or_filepath, 'rb') as f:
            result_exception = pickle.load(f)
        os.remove(queue_or_filepath)
    else:
        result_exception = queue_or_filepath.get()
    return result_exception
