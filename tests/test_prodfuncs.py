import pytest

from pyprod import main, prod

from .utils import chdir


def test_run():
    ret = prod.run("echo", "hello")
    assert ret.returncode == 0


def test_capture():
    ret = prod.capture("echo", "hello")
    assert ret == "hello"


def test_nested_command():
    # shell
    ret = prod.capture("echo", ["abc", ["def", ["ghi"]]])
    assert ret == "abc def ghi"

    # not shell
    ret = prod.capture(["echo", ["abc", ["def", ["ghi"]]]], shell=False)
    assert ret == "abc def ghi"


def test_glob(tmp_path):
    (tmp_path / "a.txt").write_text("a")

    d1 = tmp_path / "subdir1"
    d1.mkdir(parents=True)
    (d1 / "a.txt").write_text("a")
    (d1 / "b.txt").write_text("b")
    (d1 / "a.c").write_text("a")
    (d1 / ".a.c").write_text("a")

    d2 = tmp_path / "subdir1/subdir2"
    d2.mkdir(parents=True)
    (d2 / "a.txt").write_text("a")

    d3 = tmp_path / "subdir1/.subdir2"
    d3.mkdir(parents=True)
    (d3 / "a.txt").write_text("a")

    files = prod.glob("**/*.txt", tmp_path)

    assert set(files) == {
        tmp_path / "a.txt",
        d1 / "a.txt",
        d1 / "b.txt",
        d2 / "a.txt",
    }


def test_quote():
    assert prod.quote("abc", ["12 3", ["4"]]) == ["abc", "'12 3'", "4"]


def test_suote():
    assert prod.squote(["abc", ["12 3"]]) == "'abc 12 3'"


@pytest.mark.asyncio
async def test_build(tmp_path, capsys):
    src = """
@rule("a.c")
def build_a(src):
    Path(src).write_text("hello")

@task
def task1():
    print("task1")

@task
def task2():
    build("a.c", task1)
"""
    (tmp_path / "Prodfile.py").write_text(src)
    with chdir(tmp_path):
        p = prod.Prod("Prodfile.py", 4)
        ret = await p.start(["task2"])

    assert ret == 3
    assert "task1" == capsys.readouterr().out.strip()
    assert (tmp_path / "a.c").read_text() == "hello"
