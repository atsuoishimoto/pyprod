import json
import os
from contextlib import contextmanager
from pathlib import Path

import pytest

from pyprod import main, prod

from .utils import chdir

src = """
APP = "app.exe"
SRCFILES = "a.c b.c c.c".split()
OBJDIR = Path("objs")
OBJFILES = [(OBJDIR / p).with_suffix(".o") for p in SRCFILES]
HEADERS = "inc1.h inc2.h".split()
all = APP

@rule(targets=OBJDIR)
def build_dir(target):
    run("mkdir ", target)

@rule(targets=OBJDIR / "%.o", depends=("%.c",HEADERS), uses=OBJDIR)
def build_c(target, *src):
    run("cp", src[0], target)

@rule(APP, depends=OBJFILES)
def build_app(target, *src):
    run("cat", src, ">", target)

def clean():
    run("rm", "-rf", OBJDIR, OBJFILES, APP)
"""


def build_tmp_path(tmp_path):
    Path(tmp_path / "Prodfile.py").write_text(src)

    (tmp_path / "a.c").write_text("a")
    (tmp_path / "b.c").write_text("b")
    (tmp_path / "c.c").write_text("c")
    (tmp_path / "inc1.h").write_text("inc1")
    (tmp_path / "inc2.h").write_text("inc2")

    return tmp_path


@pytest.mark.asyncio
@pytest.mark.parametrize("jobs", [1, 4])
async def test_prod(tmp_path, jobs):
    build_tmp_path(tmp_path)
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", jobs)
        await p.start(["app.exe"])

    assert (tmp_path / "app.exe").is_file()
    assert (tmp_path / "objs").is_dir()
    assert (tmp_path / "objs/a.o").is_file()
    assert (tmp_path / "objs/b.o").is_file()
    assert (tmp_path / "objs/c.o").is_file()

    mtime = (tmp_path / "app.exe").stat().st_mtime
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["app.exe"])

    assert mtime == (tmp_path / "app.exe").stat().st_mtime

    (tmp_path / "a.c").write_text("aa")
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["app.exe"])

    assert mtime <= (tmp_path / "app.exe").stat().st_mtime


@pytest.mark.asyncio
async def test_pattern(tmp_path):
    src = """
@rule(targets=("a.o", "b.o"), pattern=Path("%.o"), depends=Path("%.c"))
def build(target, src):
    assert isinstance(target, str)
    Path(target).write_text(str(target))

@rule(targets=Path("%.c"))
def build_c(target):
    assert isinstance(target, str)
    Path(target).write_text(str(target))

@rule(Path("app.exe"), depends=(Path("a.o"), Path("b.o")))
def build_app(target, a, b):
    assert isinstance(target, str)
    assert isinstance(a, str)
    assert isinstance(b, str)
    Path(target).write_text(f"{target}, {a}, {b}")
"""

    (tmp_path / "Prodfile.py").write_text(src)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["app.exe"])

    assert (tmp_path / "app.exe").read_text() == "app.exe, a.o, b.o"
    assert (tmp_path / "a.o").read_text() == "a.o"
    assert (tmp_path / "a.c").read_text() == "a.c"
    assert (tmp_path / "b.o").read_text() == "b.o"
    assert (tmp_path / "b.c").read_text() == "b.c"


@pytest.mark.asyncio
async def test_dep_glob(tmp_path):
    src = """
@rule(targets=("%.o"), depends=Path("deps/%/*/dep"))
def build(target, *deps):
    assert isinstance(target, str)
    p = Path(target)
    assert set(deps) == {Path("deps/aaa/bbb/dep"), Path("deps/aaa/ccc/dep")}
    p.write_text(repr([str(p) for p in deps]))
"""

    (tmp_path / "Prodfile.py").write_text(src)

    (tmp_path / "deps/aaa/bbb/").mkdir(parents=True, exist_ok=True)
    (tmp_path / "deps/aaa/bbb/dep").write_text("1")

    (tmp_path / "deps/aaa/ccc/").mkdir(parents=True, exist_ok=True)
    (tmp_path / "deps/aaa/ccc/dep").write_text("2")

    (tmp_path / "deps/aaa/ddd/").mkdir(parents=True, exist_ok=True)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py")
        await p.start(["aaa.o"])
        print((tmp_path / "aaa.o").read_text())


@pytest.mark.asyncio
async def test_dep_glob_no_match(tmp_path):
    src = """
@rule(targets=("%.o"), depends=Path("deps/%/*/dep"))
def build(target, *deps):
    assert isinstance(target, str)
    p = Path(target)
    p.write_text(str(target)+"-"+str(deps))
"""

    (tmp_path / "Prodfile.py").write_text(src)
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py")
        await p.start(["aaa.o"])
        assert (tmp_path / "aaa.o").read_text() == "aaa.o-()"


@pytest.mark.asyncio
async def test_dep_callable(tmp_path):
    src = """
def dep1(target, stem):
    return target+".dep", stem

@rule(targets=("%.o"), depends=dep1)
def build(target, *deps):
    print(">>>>>>>>>>>>>>>>>", target, deps)
    assert deps == ("aaa.o.dep", "aaa")
"""

    (tmp_path / "Prodfile.py").write_text(src)
    (tmp_path / "aaa.o.dep").write_text("1")
    (tmp_path / "aaa").write_text("2")

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py")
        await p.start(["aaa.o"])


@pytest.mark.asyncio
async def test_uses_callable(tmp_path):
    src = """
def call1(target, stem):
    return "call1-name"

def call2(target, stem):
    return "call2-name"

@rule(targets=("%.o"), uses=(call1, call2))
def build(target, *deps):
    print(">>>>>>>>>>>>>>>>>", target, deps)
"""

    (tmp_path / "Prodfile.py").write_text(src)
    (tmp_path / "call1-name").write_text("1")

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py")
        with pytest.raises(prod.NoRuleToMakeTargetError):
            await p.start(["aaa.o"])

    (tmp_path / "call2-name").write_text("2")
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py")
        await p.start(["aaa.o"])


@pytest.mark.asyncio
async def test_preserve_pathobj(tmp_path):
    src = """
@rule(targets=Path("%.o"), depends=Path("%.c"))
def build(target, src):
    assert isinstance(target, str)
    Path(target).write_text("a")

@rule(targets=Path("%.c"))
def build_c(target):
    assert isinstance(target, str)
    Path(target).write_text(str(target))

@rule(Path("app.exe"), depends=Path("a.o"))
def build_app(target, src):
    assert isinstance(target, str)
    assert isinstance(src, str)
    Path(target).write_text("app.exe")
"""

    Path(tmp_path / "Prodfile.py").write_text(src)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["app.exe"])

    assert (tmp_path / "app.exe").read_text() == "app.exe"
    assert (tmp_path / "a.o").read_text() == "a"
    assert (tmp_path / "a.c").read_text() == "a.c"


@pytest.mark.asyncio
async def test_checker_update(tmp_path):
    src = """
import datetime
@rule(targets="a", depends="b")
def build(target, src):
    Path(target).write_text("a")

@check(targets="b")
def check(b):
    return datetime.datetime(2099,1,1,0,0,0)
"""

    (tmp_path / "Prodfile.py").write_text(src)
    (tmp_path / "a").write_text("")

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["a"])

    assert (tmp_path / "a").read_text() == "a"


@pytest.mark.asyncio
async def test_checker_no_update(tmp_path):
    src = """
import datetime
@rule(targets="a", depends="b")
def build(target, src):
    Path(target).write_text("a")

@check(targets="b")
def check(b):
    assert b == "b"
    return datetime.datetime(1999,1,1,0,0,0)
"""

    (tmp_path / "Prodfile.py").write_text(src)
    (tmp_path / "a").write_text("")

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["a"])

    assert (tmp_path / "a").read_text() == ""


@pytest.mark.asyncio
async def test_checker_no_file(tmp_path):
    src = """
import datetime
@rule(targets="a", depends="b")
def build(target, src):
    Path(target).write_text("a")
"""

    (tmp_path / "Prodfile.py").write_text(src)
    (tmp_path / "a").write_text("")

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        with pytest.raises(prod.NoRuleToMakeTargetError):
            await p.start(["a"])


@pytest.mark.asyncio
async def test_default_target(tmp_path):
    p = prod.Prod("", 4)
    p.rules.add_rule("%.a")
    p.rules.add_rule("a.a")
    assert p.get_default_target() == "a.a"


@pytest.mark.asyncio
async def test_task(tmp_path, capsys):
    src = """
@task
def task1():
    print("run-task1")
"""
    (tmp_path / "Prodfile.py").write_text(src)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["task1"])

    assert "run-task1" == capsys.readouterr().out.strip()


@pytest.mark.asyncio
async def test_task_named(tmp_path, capsys):
    src = """
@task(name="task2")
def task1():
    print("run-task2")
"""
    (tmp_path / "Prodfile.py").write_text(src)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["task2"])

    assert "run-task2" == capsys.readouterr().out.strip()


@pytest.mark.asyncio
async def test_task_uses(tmp_path, capsys):
    src = """
@rule(targets="file1")
def file1(target):
    Path(target).write_text("a")

@task(uses="file1")
def task1():
    print(f"run-task1")
"""
    (tmp_path / "Prodfile.py").write_text(src)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["task1"])

    assert "run-task1" == capsys.readouterr().out.strip()
    assert (tmp_path / "file1").read_text() == "a"


@pytest.mark.asyncio
async def test_task_uses_2(tmp_path, capsys):
    p = prod.Prod(None, 1)
    p.rules.add_rule(
        "file1",
        uses=["task1"],
        builder=lambda target: Path(target).write_text("a"),
    )
    p.rules.add_task("task1", (), False, lambda: print("run-task1"))

    with chdir(tmp_path):
        await p.start(["file1"])

    assert "run-task1" == capsys.readouterr().out.strip()
    assert (tmp_path / "file1").read_text() == "a"


@pytest.mark.asyncio
async def test_task_uses_notfound(tmp_path, capsys):
    p = prod.Prod(None, 1)
    p.rules.add_rule(
        "file1",
        uses=["task2"],
        builder=lambda target: Path(target).write_text("a"),
    )
    p.rules.add_task("task1", (), False, lambda: print("run-task1"))

    with chdir(tmp_path):
        with pytest.raises(prod.NoRuleToMakeTargetError):
            await p.start(["file1"])


@pytest.mark.asyncio
async def test_task_depended_byfunc(tmp_path, capsys):
    src = """
@task
def task1():
    print(f"run-task1")

@rule(targets="file1", uses="task1")
def file1(target):
    Path(target).write_text("a")

"""
    (tmp_path / "Prodfile.py").write_text(src)

    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        await p.start(["file1"])

    assert "run-task1" == capsys.readouterr().out.strip()
    assert (tmp_path / "file1").read_text() == "a"


@pytest.mark.asyncio
async def test_rebuild(tmp_path, capsys, mocker):
    src = """

@rule("a", depends="b")
def build_a(src, b):
    print("build")

@check("a")
def check_b(name):
    return 2

@check("b")
def check_b(name):
    return 1
"""
    (tmp_path / "Prodfile.py").write_text(src)
    main.init_args(["-r"])
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 1)
        await p.start(["a"])

    assert "build" == capsys.readouterr().out.strip()
