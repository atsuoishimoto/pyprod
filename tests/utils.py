import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def chdir(dir):
    old = Path.cwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(old)
