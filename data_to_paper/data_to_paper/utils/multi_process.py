import multiprocessing


def process_func(queue, func, *args, **kwargs):
    exception = None
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        exception = e
        result = None
    if queue:
        queue.put((result, exception))


def run_func_in_separate_process(func, *args, in_separate_process=True, **kwargs):
    if not in_separate_process:
        return process_func(None, func, *args, **kwargs)
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=process_func, args=(queue, func, *args), kwargs=kwargs)
    process.start()
    process.join()
    result = queue.get()

    return result
