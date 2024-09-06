import matplotlib

from data_to_paper.env import DEBUG_MODE

STARTED = False


def configure_matplotlib():
    global STARTED
    if not STARTED:
        STARTED = True
        matplotlib.use('Agg')
        if DEBUG_MODE:
            print('Setting MATPLOTLIB_BACKEND')
