import os
import subprocess


SYSTEM_KWARGS = {}
if os.name == 'nt':
    SYSTEM_KWARGS = {'creationflags': subprocess.CREATE_NO_WINDOW}
