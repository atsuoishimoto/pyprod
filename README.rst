PyProd: Supercharge Your Build Process with Python
===================================================

**Tired of Makefile's arcane syntax? PyProd is a modern, Python-based build tool that replaces Makefiles with the full power and simplicity of Python.**

Define complex build logic, manage dependencies, and automate your entire workflow using a language you already know and love. PyProd combines the robustness of traditional build systems with Python's vast ecosystem, creating a development experience that is more intuitive, powerful, and "makeable than make."

For detailed documentation, please refer to the `official documentation <https://pyprod.readthedocs.io/en/stable/>`_.

Why PyProd over Make?
---------------------

PyProd isn't just another Makefile clone; it's a fundamental upgrade to your build process.

*   **Write Build Logic in Pure Python:** Stop wrestling with Make's DSL and shell script workarounds. Use Python's functions, libraries, and control flow to create clear, maintainable, and powerful build scripts. Integrate directly with libraries like `boto3`, `requests`, or `pandas` for truly dynamic workflows.

*   **Automatic Virtual Environment Management:** PyProd automatically creates and manages a dedicated virtual environment for your project. This ensures a clean, isolated, and reproducible build every time, eliminating "works on my machine" issues.

*   **Dynamic & Smart Dependency Tracking:** Go beyond static file lists. PyProd can dynamically determine dependencies at runtime. It also features an optional Git-based timestamp check (`-g`), which intelligently avoids unnecessary rebuilds by checking file versions against your commit history, not just filesystem timestamps.

*   **Built-in File Watcher for Auto-Rebuilds:** Boost your productivity with a built-in file watcher. Run `pyprod --watch` and PyProd will automatically rebuild your project whenever a source file changes.

Core Features
-------------
- **Intuitive Syntax:** Define rules and tasks with simple Python decorators (`@rule`, `@task`).
- **Pattern Matching:** Create flexible, pattern-based rules, just like in Make (e.g., `"%.o": "%.c"`).
- **Parallel Execution:** Speed up your builds by running independent jobs in parallel (`-j`).
- **Extensibility:** Easily write and reuse your own Python functions for custom, complex tasks.

Installation
------------
To install PyProd, simply use pip:

.. code-block:: sh

    pip install pyprod

Quick Start: Classic C Project
------------------------------
A traditional Makefile for a C project can be elegantly expressed in a `Prodfile.py`:

.. code-block:: python

    # Prodfile.py
    CC = "gcc"
    CFLAGS = "-c -I."
    DEPS = "hello.h"
    OBJS = ["hello.o", "main.o"]
    EXE = "hello.exe"

    @rule("%.o", depends=("%.c", DEPS))
    def compile(target, src, *deps):
        run(CC, "-o", target, src, CFLAGS)

    @rule(EXE, depends=OBJS)
    def link(target, *objs):
        run(CC, "-o", target, *objs)

    @task
    def clean():
        run("rm -f", OBJS, EXE)

    @task(default=True)
    def all():
        build(EXE)

To run the build, simply execute `pyprod` in your project directory:

.. code-block:: sh

    $ pyprod

Modern Workflow: Live Reload
----------------------------

Develop faster with the built-in file watcher. PyProd will monitor your source files and trigger a rebuild automatically on any change.

.. code-block:: sh

    # Watch the 'src' and 'include' directories and rebuild on change
    $ pyprod --watch src include

Explore More
------------
You can find more advanced examples, including documentation generation and S3 file management, in the `samples <https://github.com/atsuoishimoto/pyprod/tree/main/samples>`_ directory.

License
-------
PyProd is licensed under the MIT License. See the `LICENSE <LICENSE>`_ file for more details.