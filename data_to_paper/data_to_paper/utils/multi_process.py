import multiprocessing


def process_func(queue, func, *args, **kwargs):
    result = func(*args, **kwargs)
    queue.put(result)


def run_func_in_separate_process(func, *args, **kwargs):
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=process_func, args=(queue, func, *args), kwargs=kwargs)
    process.start()
    process.join()
    result = queue.get()

    return result
