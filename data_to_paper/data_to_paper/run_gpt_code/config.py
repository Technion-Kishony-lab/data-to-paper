import matplotlib

STARTED = False


def configure_matplotlib():
    global STARTED
    if not STARTED:
        STARTED = True
        print('Setting MATPLOTLIB_BACKEND')
        matplotlib.use('Agg')
