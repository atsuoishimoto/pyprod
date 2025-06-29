PyProd: A Python-Powered Workflow Engine for Files and Beyond
================================================================

**PyProd is a modern, Python-native replacement for Makefiles. It offers both a simple, elegant way to handle traditional file-based builds and a powerful engine for orchestrating complex workflows involving any resource.**

Whether you need a more readable alternative to a Makefile for your C project, or a sophisticated system to manage data pipelines that depend on database records and S3 objects, PyProd provides a single, consistent, and powerful solution using a language you already know.

For detailed documentation, please refer to the `official documentation <https://pyprod.readthedocs.io/en/stable/>`_.

Core Features
-------------
*   **Python as the DSL:** Use pure Python for clear, maintainable, and powerful build logic.
*   **Abstract Dependency-Aware Execution:** Intelligently skips tasks based on the state of any resource, not just files.
*   **Modern Development Features:** Includes **automatic virtual environment management**, a **file watcher for auto-rebuilds** (`--watch`), and **Git-aware timestamp checking** (`-g`).

Installation (Recommended)
--------------------------

We recommend using `uv` for the best experience. `uv` is an extremely fast Python package installer and resolver.

First, install `uv`:

.. code-block:: sh

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

Then, use `uv tool install` to make the `pyprod` command available globally without polluting your system's Python environment:

.. code-block:: sh

    uv tool install pyprod

(You can also use `pip install pyprod` if you prefer.)

Quick Start: A Better Makefile
------------------------------

For those tired of Makefile's syntax, PyProd is a breath of fresh air. A classic C project build script is far more readable and maintainable when written in a `Prodfile.py`:

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

To run the build, simply execute `pyprod`:

.. code-block:: sh

    $ pyprod

But PyProd's Power Goes Far Beyond Files
----------------------------------------

The true power of PyProd is unlocked with the `@check` decorator. It allows you to define a dependency on **any resource** by writing a simple Python function. This function can check a database record, an S3 object, a Git commit, or an API response, and PyProd will only run the dependent tasks if the state of that resource changes.

This transforms PyProd into a flexible workflow engine:

*   **Depend on a Database Record:** Trigger a report only when a user is added.

    .. code-block:: python

        @check("db://users/latest")
        def check_latest_user(target):
            return db.get_latest_user_timestamp()

        @rule("report.pdf", depends="db://users/latest")
        def generate_report(target, deps):
            create_report()

*   **Depend on a Cloud Resource:** Re-run a data processing task only when an S3 object is updated.

    .. code-block:: python

        import boto3

        @check("s3://my-bucket/data.csv")
        def check_s3_object(target):
            response = boto3.client("s3").head_object(Bucket="my-bucket", Key="data.csv")
            return response["LastModified"]

Explore More
------------
You can find more advanced examples, including **S3 file management** and documentation generation, in the `samples <https://github.com/atsuoishimoto/pyprod/tree/main/samples>`_ directory. These examples showcase the true power and versatility of PyProd.

License
-------
PyProd is licensed under the MIT License. See the `LICENSE <LICENSE>`_ file for more details.
