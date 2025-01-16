PyProd - More Makeable than Make
============================================
PyProd is a Python script that can be used as an alternative to Makefile. By leveraging Python's versatility, it enables you to define build rules and dependencies programmatically, allowing for dynamic configurations, integration with existing Python libraries, and custom build logic not easily achievable with traditional Makefiles.

Features
--------
- Define build rules in Python: Use Python functions to create clear and concise build logic.
- Specify dependencies for each rule: Automatically track and resolve dependencies between files, such as source files and headers.
- Easily extendable with custom Python functions: Integrate custom logic for specialized tasks, like code linting or deployment.
- Manages virtual environments: Automatically create and manage virtual environments for each project, ensuring a clean and isolated build environment.


Example
-------
With PyProd, a traditional Makefile for C can be expressed as a Python script like this:

.. code-block:: python

    CC = "gcc"
    CFLAGS = "-c -I."
    DEPS = "hello.h"
    OBJS = "hello.o main.o".split()
    EXE = "hello.exe"

    @rule("%.o", depends=("%.c", DEPS))
    def compile(target, src, *deps):
        run(CC, "-o", target, src, CFLAGS)

    @rule(EXE, depends=OBJS)
    def link(target, *objs):
        run(CC, "-o", target, objs)

    @task
    def clean():
        run("rm -f", OBJS, "hello.exe")

    @task
    def rebuild():
        build(clean, EXE)



Other examples can be found in the `samples <https://github.com/atsuoishimoto/pyprod/tree/main/samples>`_ directory.

Table of Contents
--------------------

:doc:`quickstart`
      Get started with the PyProd.

:doc:`prodfile`
      Learn how to define build rules and dependencies in the `Prodfile.py`.

:doc:`commandline`
      Command line options for running the build script.



.. Hidden TOCs

.. toctree::
   :caption: PyProd Documentation
   :hidden:

   quickstart
   prodfile
   commandline
   releasenotes
   



