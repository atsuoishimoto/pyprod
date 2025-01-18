# ruff: NOQA
# type: ignore

DOC = "DOC.txt"
SRCFILES = "a.txt b.txt c.txt".split()
BUILDDIR = Path("build")
BUILDFILES = [(BUILDDIR / p).with_suffix(".o") for p in SRCFILES]
COMMON = "inc1.txt inc2.txt".split()


@rule(DOC, depends=BUILDFILES)
def build_app(target, *src):
    run("cat", *src, ">", target)


@rule(BUILDDIR)
def build_dir(target):
    run("mkdir -p", target)


@rule(BUILDDIR / "%.o", depends=("%.txt", COMMON), uses=BUILDDIR)
def build_c(target, src, *commons):
    run("cat", *commons, src, ">", target)


@task
def clean():
    run("rm", "-rf", BUILDDIR, BUILDFILES, DOC)


@task
def rebuild():
    build(clean, DOC)
