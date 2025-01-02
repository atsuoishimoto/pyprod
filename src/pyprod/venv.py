import os
import subprocess
import sys
import sysconfig
import threading
import venv
from pathlib import Path

import pyprod

from .utils import flatten

THREADID = threading.get_ident()
pyprodenv = ".pyprod"
venvdir = None

PYPRODVENV = ".pyprod"


def makevenv(conffile):
    global venvdir
    venvdir = Path(".") / f".{conffile.name}{PYPRODVENV}"
    if not venvdir.is_dir():
        venv.main([str(venvdir)])

    purelib = sysconfig.get_path(
        "purelib", scheme="venv", vars={"base": str(venvdir.resolve())}
    )
    sys.path.insert(0, purelib)

    os.environ["VIRTUAL_ENV"] = str(venvdir)
    os.environ["PATH"] = os.path.pathsep.join(
        [str(venvdir / "bin"), os.environ["PATH"]]
    )


def pip(*args):
    if THREADID != threading.get_ident():
        raise RuntimeError("pip() should not be called in workder thread")

    if not venvdir:
        makevenv(pyprod.modulefile)
    args = flatten(args)
    subprocess.run(
        [venvdir / "bin/python", "-m", "pip", "--no-input", "install", *args],
        check=True,
    )
