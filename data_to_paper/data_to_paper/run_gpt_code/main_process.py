import multiprocessing
import pickle

import my_module
from my_module import MyClass


def subprocess_task_1(cls):
    print("Subprocess sees:", cls.a)


def subprocess_task_2(cls):
    cls.a = 3
    print("Subprocess sees:", MyClass.a)


if __name__ == '__main__':
    # Modify the attribute in the main process
    MyClass.a = 2
    print("Main process sees:", MyClass.a)

    print("Pickle: ", pickle.loads(pickle.dumps(MyClass)).a)

    p = multiprocessing.Process(target=subprocess_task_1, args=(my_module,))
    p.start()
    p.join()

    p = multiprocessing.Process(target=subprocess_task_2, args=(MyClass,))
    p.start()
    p.join()
