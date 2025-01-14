import asyncio
import concurrent.futures
import datetime
import importlib
import importlib.machinery
import importlib.util
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict
from collections.abc import Collection
from dataclasses import dataclass, field
from fnmatch import fnmatch, translate
from pathlib import Path

import pyprod

from .utils import flatten, unique_list
from .venv import pip

logger = logging.getLogger(__name__)


class CircularReferenceError(Exception):
    pass


class NoRuleToMakeTargetError(Exception):
    pass


class RuleError(Exception):
    pass


class TargetError(Exception):
    pass


class HandledExceptionError(Exception):
    pass


omit = object()


def run(
    *args,
    echo=True,
    shell=None,
    stdout=False,
    cwd=None,
    text=True,
    check=True,
):
    match args:
        case [[*tokens]]:
            if shell is None:
                shell = False
            args = [list(str(t) for t in flatten(tokens))]
            sargs = str(tokens)
        case _:
            args = [" ".join(str(a) for a in flatten(args))]
            sargs = args[0]
            if shell is None:
                shell = True

    if stdout is True:
        stdout = subprocess.PIPE
    elif stdout is False:
        stdout = None

    if echo:
        print("run: %s" % sargs, file=sys.stderr)
    try:
        ret = subprocess.run(
            *args, cwd=cwd, shell=shell, stdout=stdout, text=text, check=check
        )
    except subprocess.CalledProcessError as e:
        match pyprod.verbose:
            case 0:
                logger.debug("command failed: %s %s", str(e), sargs)
            case _:
                logger.warning("command failed: %s %s", str(e), sargs)

        raise HandledExceptionError() from e

    return ret


def capture(*args, echo=True, cwd=None, check=True, text=True, shell=None):
    ret = run(
        *args, echo=echo, cwd=cwd, check=check, text=text, stdout=True, shell=shell
    )
    ret = ret.stdout or ""
    ret = ret.rstrip("\n")
    return ret


def glob(path, dir="."):
    ret = []
    for c in Path(dir).glob(path):
        # ignore dot files
        if any(p.startswith(".") for p in c.parts):
            continue
        ret.append(c)
    return ret


def rule_to_re(rule):
    if not isinstance(rule, (str, Path)):
        raise TypeError(f"str or Path required: {rule}")

    srule = str(rule)
    srule = translate(srule)
    srule = replace_pattern(srule, "(?P<stem>.*)", maxreplace=1)
    return srule


def replace_pattern(rule, replaceto, *, maxreplace=None):
    n = 0
    s_rule = str(rule)

    def f(m):
        nonlocal n
        if len(m[0]) == 2:
            return "%"
        else:
            n += 1
            if maxreplace is not None:
                if n > maxreplace:
                    # contains multiple '%'
                    raise RuleError(f"{s_rule} contains multiple '%'")

            return replaceto

    s_rule = re.sub("%%|%", f, s_rule)
    return s_rule


def _check_pattern_count(pattern):
    """Counts number of '%' in the pattern"""
    matches = re.finditer(r"%%|%", pattern)
    num = len([m for m in matches if len(m[0]) == 1])
    if num > 1:
        raise RuleError(f"{pattern}: Multiple '%' is not allowed")
    return num


def _check_pattern(pattern):
    matches = re.finditer(r"%%|%", pattern)
    singles = [m for m in matches if len(m[0]) == 1]
    if len(singles) > 1:
        raise RuleError(f"{pattern}: Multiple '%' is not allowed")
    if not len(singles):
        raise RuleError(f"{pattern}: Pattern should contain a '%'.")


def _check_wildcard(path):
    if "*" in path:
        raise RuleError(f"{path}: '*' directory is not allowed")


def _name_to_str(name):
    match name:
        case _TaskFunc():
            return name.name
        case Path():
            return str(name)
        case str():
            return name

    return name


class Rule:
    def __init__(
        self, targets, pattern=None, depends=(), uses=(), builder=None, name=None
    ):
        self.targets = []
        self.first_target = None
        if targets:
            for target in flatten(targets):
                if not target:
                    continue
                target = str(target)
                if not target:
                    continue

                if not self.first_target:
                    if "*" not in target:
                        if _check_pattern_count(target) == 0:
                            # not contain one %
                            self.first_target = target

                target = rule_to_re(target)
                self.targets.append(target)

        if pattern:
            pattern = str(pattern)
            if _check_pattern_count(pattern) != 1:
                raise RuleError(f"{pattern}: Pattern should contain a '%'")

            self.pattern = rule_to_re(pattern)
        else:
            self.pattern = None

        self.depends = []
        for depend in flatten(depends or ()):
            depend = _name_to_str(depend)
            _check_pattern_count(depend)
            _check_wildcard(depend)
            self.depends.append(depend)

        self.uses = []
        for use in flatten(uses or ()):
            use = _name_to_str(use)
            _check_pattern_count(use)
            _check_wildcard(use)
            self.uses.append(use)

        self.builder = builder
        self.name = _name_to_str(name)

    def __call__(self, f):
        self.builder = f
        return f


class _TaskFunc:
    def __init__(self, f, name):
        self.f = f
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)


class Task(Rule):
    def __init__(self, name, depends, uses, func=None):
        super().__init__(
            (), pattern=None, depends=depends, uses=uses, builder=func, name=name
        )
        if name:
            self.targets = [name]
            self.first_target = True

        if func:
            self._set_funcname(func)

    def _set_funcname(self, f):
        if not self.name:
            if not f.__name__ or f.__name__ == "<lambda>":
                raise RuleError(
                    "Task function should have a name. Use @task(name='name')"
                )
            self.name = f.__name__
            self.targets = [f.__name__]

        self.first_target = True

    def __call__(self, f):
        self.builder = f
        self._set_funcname(f)
        return _TaskFunc(f, self.name)
        return f


class Rules:
    def __init__(self):
        self.rules = []
        self.tree = defaultdict(set)
        self._detect_loop = set()
        self.frozen = False

    def add_rule(self, targets, pattern=None, depends=(), uses=(), builder=None):
        if self.frozen:
            raise RuntimeError("No new rule can be added after initialization")

        dep = Rule(targets, pattern, depends, uses, builder)
        self.rules.append(dep)
        return dep

    def add_task(self, name=None, depends=(), uses=(), func=None):
        if self.frozen:
            raise RuntimeError("No new rule can be added after initialization")

        dep = Task(name, depends, uses, func)
        self.rules.append(dep)
        return dep

    def rule(self, target, *, pattern=None, depends=(), uses=()):
        dep = self.add_rule([target], pattern, depends, uses, None)
        return dep

    def task(self, func=None, *, name=None, depends=(), uses=()):
        dep = self.add_task(name, depends, uses, func)
        return dep

    def iter_rule(self, name):
        name = _name_to_str(name)
        for dep in self.rules:
            for target in dep.targets:
                m = re.fullmatch(target, name)
                if m:
                    stem = None
                    d = m.groupdict().get("stem", None)
                    if d is not None:
                        stem = d
                    elif dep.pattern:
                        m = re.fullmatch(dep.pattern, name)
                        if m:
                            stem = m.groupdict().get("stem", None)

                    if stem is not None:
                        depends = [replace_pattern(r, stem) for r in dep.depends]
                        uses = [replace_pattern(r, stem) for r in dep.uses]
                    else:
                        depends = dep.depends[:]
                        uses = dep.uses[:]

                    yield depends, uses, dep
                    break

    def get_dep_names(self, name):
        assert name
        ret_depends = []
        ret_uses = []

        for depends, uses, dep in self.iter_rule(name):
            if dep.builder:
                continue

            ret_depends.extend(depends)
            ret_uses.extend(uses)

        return unique_list(ret_depends), unique_list(ret_uses)

    def select_first_target(self):
        for dep in self.rules:
            if dep.first_target:
                return dep.first_target

    def select_builder(self, name):
        for depends, uses, dep in self.iter_rule(name):
            if not dep.builder:
                continue
            return depends, uses, dep

    def build_tree(self, name, lv=1):
        self.frozen = True

        name = _name_to_str(name)
        if name in self._detect_loop:
            raise CircularReferenceError(f"Circular reference detected: {name}")

        self._detect_loop.add(name)
        try:
            if name in self.tree:
                return
            deps, uses = self.get_dep_names(name)
            depends = deps + uses

            selected = self.select_builder(name)
            if selected:
                build_deps, build_uses, _ = selected
                depends.extend(build_deps)
                depends.extend(build_uses)

            depends = unique_list(depends)
            self.tree[name].update(depends)
            for dep in depends:
                self.build_tree(dep, lv=lv + 1)

        finally:
            self._detect_loop.remove(name)


class Checkers:
    def __init__(self):
        self.checkers = []

    def get_checker(self, name):
        name = _name_to_str(name)
        for targets, f in self.checkers:
            for target in targets:
                if fnmatch(name, target):
                    return f

    def add_check(self, target, f):
        target = list(map(_name_to_str, flatten(target or ())))
        self.checkers.append((target, f))

    def check(self, target):
        def deco(f):
            self.add_check(target, f)
            return f

        return deco


MAX_TS = 1 << 63


def is_file_exists(name):
    return os.path.getmtime(name)


class Exists:
    def __init__(self, name, exists, ts=None):
        self.name = name
        self.exists = exists
        self.ts = ts if exists else 0

    def __repr__(self):
        return f"Exists({self.name!r}, {self.exists!r}, {self.ts!r})"


class Params:
    def __init__(self, params):
        if params:
            self.__dict__.update(params)

    def __getattr__(self, name):
        # never raise AttributeError
        return ""

    def get(self, name, default=None):
        # hasattr cannot be used since __getattr__ never raise AttributeError
        if name in self.__dict__:
            return getattr(self, name)
        else:
            return default


class Envs:
    def __getattr__(self, name):
        return os.environ.get(name, "")

    def __setattr__(self, name, value):
        os.environ[name] = str(value)

    def __getitem__(self, name):
        return os.environ.get(name, "")

    def __setitem__(self, name, value):
        os.environ[name] = str(value)

    def __delitem__(self, name):
        if name in os.environ:
            del os.environ[name]

    def get(self, name, default=None):
        return os.environ.get(name, default=default)


def read(filename):
    with open(filename, "r") as f:
        return f.read()


def write(filename, s, append=False):
    mode = "a" if append else "w"
    with open(filename, mode) as f:
        f.write(s)


def quote(*s):
    ret = [shlex.quote(str(x)) for x in flatten(s)]
    return ret


def squote(s):
    s = " ".join(str(e) for e in flatten(s))
    return shlex.quote(s)


def makedirs(path):
    os.makedirs(path, exist_ok=True)


class Prod:
    def __init__(self, modulefile, njobs=1, params=None):
        if modulefile:
            self.modulefile = Path(modulefile)
        else:
            self.modulefile = None

        self.rules = Rules()
        self.checkers = Checkers()
        if njobs > 1:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=njobs)
        else:
            self.executor = None
        self.params = Params(params)
        self.buildings = {}
        self.module = None
        if self.modulefile:
            self.module = self.load_pyprodfile(self.modulefile)
        self.built = 0  # number of build execused

    def get_module_globals(self):
        globals = {
            "capture": capture,
            "check": self.checkers.check,
            "environ": Envs(),
            "glob": glob,
            "makedirs": makedirs,
            "os": os,
            "params": self.params,
            "pip": pip,
            "quote": quote,
            "q": quote,
            "squote": squote,
            "sq": squote,
            "read": read,
            "rule": self.rules.rule,
            "run": run,
            "shutil": shutil,
            "task": self.rules.task,
            "write": write,
            "MAX_TS": MAX_TS,
            "Path": Path,
        }
        return globals

    def load_pyprodfile(self, pyprodfile: Path) -> dict:
        spath = os.fspath(pyprodfile)
        loader = importlib.machinery.SourceFileLoader(pyprodfile.stem, spath)
        spec = importlib.util.spec_from_file_location(
            pyprodfile.stem, spath, loader=loader
        )
        mod = importlib.util.module_from_spec(spec)

        # exec module
        mod.__dict__.update(self.get_module_globals())

        spec.loader.exec_module(mod)
        return mod

    async def run_in_executor(self, func, *args, **kwargs):
        if self.executor:
            loop = asyncio.get_running_loop()
            ret = await loop.run_in_executor(
                self.executor, lambda: func(*args, **kwargs)
            )
        else:
            ret = func(*args, **kwargs)

        return ret

    def get_default_target(self):
        return self.rules.select_first_target()

    async def start(self, deps):
        self.built = 0
        names = []
        for name in deps:
            if isinstance(name, str):
                value = getattr(self.module, name, None)
                if value:
                    names.append(value)
                else:
                    names.append(name)
            else:
                names.append(name)

        builds = []
        waitings = []
        for obj in flatten(names):
            if isinstance(obj, str | Path):
                builds.append(obj)
            elif isinstance(obj, Rule):
                raise TargetError(f"Invalid target specified: {obj}")
            elif callable(obj):
                self.built += 1
                task = asyncio.create_task(self.run_in_executor(obj))
                waitings.append(task)
            else:
                raise TargetError(f"Invalid target specified: {obj}")

        await self.build(builds)
        await asyncio.gather(*waitings)
        return self.built

    async def build(self, deps):
        tasks = []
        waits = []
        for dep in deps:
            if dep not in self.buildings:
                ev = asyncio.Event()
                self.buildings[dep] = ev
                task = self.run(dep)
                tasks.append((dep, task))
                waits.append(ev)
            else:
                obj = self.buildings[dep]
                if isinstance(obj, asyncio.Event):
                    waits.append(obj)

        for dep, task in tasks:
            ev = self.buildings[dep]
            try:
                self.buildings[dep] = await task
            finally:
                ev.set()

        events = [ev.wait() for ev in waits]
        await asyncio.gather(*events)

        ts = []
        for dep in deps:
            obj = self.buildings[dep]
            if isinstance(obj, int | float):
                ts.append(obj)
        if ts:
            return max(ts)
        return 0

    async def is_exists(self, name):
        checker = self.checkers.get_checker(name)
        try:
            if checker:
                ret = await self.run_in_executor(checker, name)
            else:
                ret = await self.run_in_executor(is_file_exists, name)
        except FileNotFoundError:
            ret = False

        if not ret:
            return Exists(name, False)
        if isinstance(ret, datetime.datetime):
            ret = ret.timestamp()
        if ret < 0:
            ret = MAX_TS
        return Exists(name, True, ret)

    async def run(self, name):  # -> Any | int:
        name = _name_to_str(name)

        self.rules.build_tree(name)
        deps, uses = self.rules.get_dep_names(name)
        selected = self.rules.select_builder(name)
        if selected:
            build_deps, build_uses, builder = selected
            deps = deps + build_deps
            uses = uses + build_uses

        ts = 0
        if deps:
            ts = await self.build(deps)
        if uses:
            await self.build(uses)

        if selected and isinstance(builder, Task):
            await self.run_in_executor(builder.builder, *build_deps)
            return MAX_TS

        exists = await self.is_exists(name)

        if not exists.exists:
            logger.debug("%r does not exists", name)
        elif (ts >= MAX_TS) or (exists.ts < ts):
            logger.debug("%r should be updated", name)
        else:
            logger.debug("%r already exists", name)

        if not exists.exists and not selected:
            raise NoRuleToMakeTargetError("No rule to make target: {name}")

        elif selected and ((not exists.exists) or (ts >= MAX_TS) or (exists.ts < ts)):
            logger.warning("building: %r", name)
            await self.run_in_executor(builder.builder, name, *build_deps)
            self.built += 1
            return MAX_TS

        return max(ts, exists.ts)
