from pathlib import Path
import os
from contextlib import contextmanager

@contextmanager
def chdir(dir):
    old = Path.cwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(old)

