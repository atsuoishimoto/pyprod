"""
Sample Prodfile for building a C program.
"""

# ruff: NOQA
# type: ignore

APP = "hello.exe"
CC = "gcc"
CFLAGS = "-c -I."
DEPS = "hello.h"
OBJS = "hello.o main.o".split()


@rule(APP, depends=OBJS)
def link(target, *src):
    """
    Build executable
    """
    run(CC, "-o", target, src)


@rule("%.o", depends=("%.c", DEPS))
def compile(target, src, *deps):
    run(CC, "-o", target, src, CFLAGS)


@task
def clean():
    """
    Remove the built files.
    """
    run("rm", "-rf", OBJS, APP)


@task
def rebuild():
    """
    Clean and rebuild all files.
    """
    build(clean, APP)
