from pyprod import prod


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


def test_squote():
    assert prod.squote("abc", ["12 3"]) == ["abc", "'12 3'"]
