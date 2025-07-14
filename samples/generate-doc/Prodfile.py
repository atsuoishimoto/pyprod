# ruff: NOQA
# type: ignore

"""
Sample Prodfile.py to concatenate text files.
"""

DOC = "DOC.txt"
SRCFILES = ["a.txt", "b.txt", "c.txt"]
BUILDDIR = Path("build")
COMMON = ["inc1.txt", "inc2.txt"]


@rule(DOC, depends=(SRCFILES, COMMON))
def build_app(target, *src):
    """Builds target text"""
    run("cat", *src, ">", target)


@rule(BUILDDIR)
def build_dir(target):
    run("mkdir -p", target)


@task
def clean():
    run("rm", "-rf", BUILDDIR, DOC)


@task
def rebuild():
    build(clean, DOC)
