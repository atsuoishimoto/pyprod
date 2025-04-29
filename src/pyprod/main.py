import argparse
import asyncio
import logging
import os
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import pyprod
import pyprod.prod

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description="""PyProd - More makable than make""",
)

parser.add_argument(
    "-C",
    "--directory",
    dest="directory",
    help="Change to DIRECTORY before performing any operations",
)

parser.add_argument(
    "-f", "--file", help="Use FILE as the Prodfile (default: 'Prodfile.py')"
)

parser.add_argument(
    "-j",
    "--job",
    type=int,
    default=1,
    help="Allow up to N jobs to run simultaneously (default: 1)",
)

parser.add_argument(
    "-r", "--rebuild", dest="rebuild", action="store_true", help="Rebuild all"
)

parser.add_argument(
    "-g",
    "--use-git",
    dest="use_git",
    action="store_true",
    help="Get file timestamps from Git",
)

parser.add_argument(
    "-w",
    "--watch",
    nargs="*",
    help="directories to watch",
)

parser.add_argument(
    "-v",
    dest="verbose",
    action="count",
    default=0,
    help="Increase verbosity level (default: 0)",
)

parser.add_argument(
    "-V",
    "--version",
    dest="version",
    action="store_true",
    default=0,
    help="Show version",
)


parser.add_argument("targets", nargs="*", help="Build targets")


def print_exc(e):
    match pyprod.args.verbose:
        case 0:
            logger.error("%s: %s", type(e).__name__, e)
        case 1:
            logger.error("%r", e)
        case _:
            logger.exception("Terminated by exception")


def init_args(args=None):
    args = pyprod.args = parser.parse_args(args)
    return args


class Handler(FileSystemEventHandler):
    def __init__(self, ev):
        self._ev = ev

    def on_created(self, event):
        print(event)
        self._ev.set()

    def on_modified(self, event):
        print(event)
        self._ev.set()

    def on_deleted(self, event):
        print(event)
        self._ev.set()


def main():
    args = init_args()
    if args.version:
        print(f"PyProd {pyprod.__version__}")
        sys.exit(0)

    pyprod.verbose = args.verbose
    chdir = args.directory
    if chdir:
        os.chdir(chdir)

    if "" not in sys.path:
        sys.path.insert(0, "")

    match args.verbose:
        case 0:
            level = logging.ERROR
        case 1:
            level = logging.INFO
        case _:
            level = logging.DEBUG

    logging.basicConfig(level=level, format="%(asctime)s: %(message)s")

    if args.file:
        pyprodfiles = [args.file]
    else:
        pyprodfiles = ["Prodfile.py"]

    for mod in pyprodfiles:
        mod = pyprod.modulefile = Path(mod)
        if mod.is_file():
            break
    else:
        sys.exit("No make module found")

    params = {}
    targets = []

    for target in args.targets:
        if "=" in target:
            name, value = target.split("=", 1)
            params[name] = value
        else:
            targets.append(target)

    run(mod, args.job, params, targets)

    if args.watch:
        ev = threading.Event()
        observer = Observer()

        for watch in args.watch:
            d = Path(watch).absolute()
            print(d)
            observer.schedule(Handler(ev), str(d), recursive=True)

        observer.start()
        while True:
            ev.wait()
            time.sleep(0.1)
            ev.clear()
            run(mod, args.job, params, targets)


def run(mod, job, params, targets):
    try:
        # load module
        prod = pyprod.prod.Prod(mod, job, params)
        # select targets
        if not targets:
            target = prod.get_default_target()
            if not target:
                sys.exit("No default target")
            targets = [target]

        ret = asyncio.run(prod.start(targets))
        if not ret:
            print(f"Nothing to be done for {targets}")

    except pyprod.prod.HandledExceptionError:
        # ignored
        pass
    except Exception as e:
        print_exc(e)
