import os
import subprocess


SYSTEM_KWARGS = {}
if os.name == 'nt':
    SYSTEM_KWARGS = {'creationflags': subprocess.CREATE_NO_WINDOW}


def get_subprocess_kwargs(capture: bool = True):
    if capture:
        return {'check': True, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, **SYSTEM_KWARGS}
    return {'check': True, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL, **SYSTEM_KWARGS}
