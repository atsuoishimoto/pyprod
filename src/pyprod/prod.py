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
from functools import wraps
from pathlib import Path

import dateutil.parser

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
    root = Path(dir)
    for c in root.glob(path):
        # ignore dot files
        if any((p not in (".", "..")) and p.startswith(".") for p in c.parts):
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
        raise RuleError(f"{path}: '*' is not allowed")


def _name_to_str(name):
    match name:
        case Task():
            return name.name
        case _TaskFunc():
            return name.name
        case Path():
            return str(name)
        case str():
            return name
        case _:
            raise ValueError(f"Invalid dependency name: {name}")

    return name


def _expand_glob(name):
    if not isinstance(name, (str, Path)):
        return name

    if "*" not in str(name):
        return name

    # split path to support absolute path
    p = Path(name)
    parts = p.parts
    for i, part in enumerate(parts):
        if "*" in part:
            root = Path(*parts[:i])
            rest = "/".join(parts[i:])
            break

    return list(root.glob(rest))


class Rule:
    def __init__(self, targets, pattern=None, depends=(), uses=(), builder=None):
        self.targets = []
        self.default = False
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
            if not depend:
                continue

            if not callable(depend):
                depend = _name_to_str(depend)
                _check_pattern_count(depend)
            self.depends.append(depend)

        self.uses = []
        for use in flatten(uses or ()):
            if not use:
                continue

            if not callable(use):
                use = _name_to_str(use)
                _check_pattern_count(use)
                _check_wildcard(use)
            self.uses.append(use)

        self.builder = builder

    def __call__(self, f):
        self.builder = f
        return f


class _TaskFunc:
    def __init__(self, f, name):
        self.f = f
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)


def default_builder(*args, **kwargs):
    # default builder
    pass


class Task(Rule):
    def __init__(self, name, uses, default, func=None):
        super().__init__((), pattern=None, depends=(), uses=uses, builder=func)
        if name:
            self.name = _name_to_str(name)
            if name:
                self.targets = [name]
                self.first_target = self.name
        else:
            self.name = None

        self.default = default
        if func:
            self._set_funcname(func)
        if not self.builder:
            self.builder = default_builder

    def _set_funcname(self, f):
        if not self.name:
            if not f.__name__ or f.__name__ == "<lambda>":
                raise RuleError(
                    "Task function should have a name. Use @task(name='name')"
                )
            self.name = f.__name__
            self.targets = [f.__name__]

        self.first_target = self.name

    def __call__(self, f):
        self.builder = f
        self._set_funcname(f)
        return _TaskFunc(f, self.name)


class Rules:
    def __init__(self):
        self.rules = []
        self.tree = defaultdict(set)
        self._detect_loop = set()
        self.frozen = False

    def add_rule(self, targets, pattern=None, depends=(), uses=(), builder=None):
        if builder:
            if not callable(builder):
                raise ValueError(f"{builder} is not callable")

        if self.frozen:
            raise RuntimeError("No new rule can be added after initialization")

        dep = Rule(targets, pattern, depends, uses, builder)
        self.rules.append(dep)
        return dep

    def add_task(self, name=None, uses=(), default=False, func=None):
        if self.frozen:
            raise RuntimeError("No new rule can be added after initialization")
        dep = Task(name, uses, default, func)
        self.rules.append(dep)
        return dep

    def rule(self, targets, *, pattern=None, depends=(), uses=()):
        if not targets:
            raise ValueError("No target specified")

        dep = self.add_rule([targets], pattern, depends, uses, None)
        return dep

    def task(self, func=None, *, name=None, uses=(), default=False):
        if func:
            if not callable(func):
                raise ValueError(f"{func} is not callable")

        dep = self.add_task(name, uses, default, func)
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

                    depends = []
                    for d in dep.depends:
                        if callable(d):
                            ret = flatten([d(name, stem)], ignore_none=True)
                            depends.extend(ret)
                        else:
                            depends.append(d)

                    uses = []
                    for u in dep.uses:
                        if callable(u):
                            ret = flatten([u(name, stem)], ignore_none=True)
                            uses.extend(ret)
                        else:
                            uses.append(u)

                    if stem is not None:
                        depends = [replace_pattern(r, stem) for r in depends]
                        uses = [replace_pattern(r, stem) for r in uses]
                    else:
                        depends = dep.depends[:]
                        uses = dep.uses[:]

                    depends = list(flatten(_expand_glob(depend) for depend in depends))
                    yield depends, uses, dep
                    break

    def get_dep_names(self, name):
        ret_depends = []
        ret_uses = []

        for depends, uses, dep in self.iter_rule(name):
            if dep.builder:
                continue

            ret_depends.extend(depends)
            ret_uses.extend(uses)

        return unique_list(ret_depends), unique_list(ret_uses)

    def select_first_target(self):
        first = None
        for dep in self.rules:
            if dep.default and (not first):
                first = dep.name

            if dep.first_target:
                return dep.first_target

        return first

    def select_builder(self, name):
        for depends, uses, dep in self.iter_rule(name):
            if not dep.builder:
                continue
            return depends, uses, dep

    def build_tree(self, name, lv=1):
        assert name
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

    def add_check(self, targets, f):
        targets = list(map(_name_to_str, flatten(targets or ())))
        self.checkers.append((targets, f))

    def check(self, targets):
        def deco(f):
            self.add_check(targets, f)
            return f

        return deco


MAX_TS = 1 << 63


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
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)
        else:
            self.executor = None
        self.params = Params(params)
        self.use_git_timestamp = pyprod.args.use_git

        self.buildings = {}
        self.module = None
        if self.modulefile:
            self.module = self.load_pyprodfile(self.modulefile)
        self.built = 0  # number of build execused

        self.deps = []

    def get_module_globals(self):
        globals = {
            "build": self.build,
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
            "use_git": self.use_git,
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

    def get_file_mtime(self, name):
        return os.path.getmtime(name)

    def get_file_mtime_git(self, name):
        ret = subprocess.check_output(
            ["git", "log", "-1", "--format=%ai", "--", name], text=True
        ).strip()
        if not ret:
            logger.warning("%s did not match any file in git", name)
            return self.get_file_mtime(name)

        # 2025-01-17 00:05:48 +0900
        return dateutil.parser.parse(ret)

    async def is_exists(self, name):
        checker = self.checkers.get_checker(name)
        try:
            if checker:
                ret = await self.run_in_executor(checker, name)
            elif self.use_git_timestamp:
                ret = await self.run_in_executor(self.get_file_mtime_git, name)
            else:
                ret = await self.run_in_executor(self.get_file_mtime, name)
        except FileNotFoundError:
            ret = False

        if isinstance(ret, FileNotFoundError):
            ret = False

        if not ret:
            return Exists(name, False)
        if isinstance(ret, datetime.datetime):
            ret = ret.timestamp()
        if ret < 0:
            ret = MAX_TS
        return Exists(name, True, ret)

    def build(self, *deps):
        if deps:
            self.deps[0:0] = deps

    def use_git(self, use):
        self.use_git_timestamp = use

    def get_default_target(self):
        return self.rules.select_first_target()

    async def start(self, deps):
        self.loop = asyncio.get_running_loop()
        self.built = 0
        self.deps.append(deps)
        while self.deps:
            tasks = []
            dep = self.deps.pop(0)
            tasks.append(self.schedule([dep]))
            await asyncio.gather(*tasks)

        return self.built

    async def schedule(self, deps):
        deps = list(flatten(deps))
        tasks = []
        waits = []
        for dep in deps:
            if dep not in self.buildings:
                ev = asyncio.Event()
                self.buildings[dep] = ev
                coro = self.run(dep)
                tasks.append((dep, coro))
                waits.append(ev)
            else:
                obj = self.buildings[dep]
                if isinstance(obj, asyncio.Event):
                    waits.append(obj)

        results = await asyncio.gather(*(coro for _, coro in tasks))
        for ret, (dep, _) in zip(results, tasks):
            ev = self.buildings[dep]
            try:
                self.buildings[dep] = ret
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

    async def run(self, name):  # -> Any | int:
        name = _name_to_str(name)
        self.rules.build_tree(name)
        deps, uses = self.rules.get_dep_names(name)
        selected = self.rules.select_builder(name)
        if selected:
            build_deps, build_uses, builder = selected
            deps = deps + build_deps
            uses = uses + build_uses

        tasks = []
        if deps:
            deps_task = asyncio.create_task(self.schedule(deps))
            tasks.append(deps_task)
        if uses:
            uses_task = self.schedule(uses)
            tasks.append(uses_task)

        await asyncio.gather(*tasks)
        ts = 0
        if deps:
            ts = deps_task.result()

        if selected and isinstance(builder, Task):
            self.built += 1
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
            raise NoRuleToMakeTargetError(f"No rule to make target: {name}")

        elif selected and (
            (not exists.exists)
            or (ts >= MAX_TS)
            or (exists.ts < ts)
            or pyprod.args.rebuild
        ):
            logger.warning("building: %r", name)
            await self.run_in_executor(builder.builder, name, *build_deps)
            self.built += 1
            return MAX_TS

        return max(ts, exists.ts)
