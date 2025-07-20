Getting Started
===============

Welcome to PyProd! This section will help you get up and running quickly with PyProd,
a modern Python-based build automation tool that serves as a powerful alternative to Make.

Why PyProd?
-----------

If you've ever struggled with Makefile syntax or wished you could use Python's power
in your build system, PyProd is for you. It offers:

* **Pythonic syntax** - Write build rules in clear, readable Python
* **Smart dependency tracking** - Automatically rebuild only what's needed
* **Beyond files** - Depend on S3 objects, APIs, databases, or any custom resource
* **Modern features** - Built-in watch mode, parallel execution, and more

What You'll Learn
-----------------

This Getting Started guide covers everything you need to begin using PyProd effectively:

.. toctree::
   :maxdepth: 1
   
   installation
   quickstart
   first-project

Quick Overview
--------------

Here's a taste of PyProd - a simple C project build configuration:

.. code-block:: python

    # Prodfile.py (instead of Makefile)
    from pyprod import rule, task, run

    @rule("%.o", depends="%.c")
    def compile(target, source):
        run("gcc", "-c", source, "-o", target)

    @rule("app", depends=["main.o", "utils.o"])
    def link(target, *objects):
        run("gcc", *objects, "-o", target)

    @task(default=True)
    def build():
        run("pyprod app")

    @task
    def clean():
        run("rm", "-f", "*.o", "app")

Compare this to a traditional Makefile - the Python version is clearer, more maintainable,
and gives you access to Python's entire ecosystem.

Recommended Path
----------------

1. **Install PyProd** (:doc:`installation`)
   
   Start with our recommended ``uv`` installation method for the best experience:
   
   .. code-block:: bash
   
       uv tool install pyprod

2. **Try the Quickstart** (:doc:`quickstart`)
   
   Learn the basics in 5 minutes with hands-on examples of tasks, rules, and patterns.

3. **Build Your First Project** (:doc:`first-project`)
   
   Walk through creating a complete project with PyProd, including:
   
   - Setting up a Prodfile.py
   - Defining build rules
   - Managing dependencies
   - Running parallel builds
   - Using watch mode

Prerequisites
-------------

* Python 3.10 or higher
* Basic familiarity with command-line tools
* Understanding of build systems concepts (helpful but not required)

Getting Help
------------

* **Examples**: Check the ``samples/`` directory in the `PyProd repository <https://github.com/atsuoishimoto/pyprod>`_
* **Issues**: Report bugs or request features on `GitHub <https://github.com/atsuoishimoto/pyprod/issues>`_
* **Discussions**: Ask questions in the `GitHub Discussions <https://github.com/atsuoishimoto/pyprod/discussions>`_

Ready to Begin?
---------------

Let's start with :doc:`installation` to get PyProd set up on your system!