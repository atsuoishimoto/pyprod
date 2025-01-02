# ruff: NOQA
# type: ignore

APP = "hello.exe"
CC = "gcc"
CFLAGS = "-I."
DEPS = "hello.h"
OBJS = "hello.o main.o".split()


@rule(APP, depends=OBJS)
def link(target, *src):
    run(CC, "-o", target, src)


@rule("%.o", depends=("%.c", DEPS))
def compile(target, src, *deps):
    run(CC, "-c -o", target, src, CFLAGS)


def clean():
    run("rm", "-rf", OBJS, APP)


all = APP
