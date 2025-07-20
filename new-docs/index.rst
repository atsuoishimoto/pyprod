PyProd Documentation
===================

PyProd is a modern, Python-based build automation tool that serves as a powerful alternative to Make.

Why PyProd?
-----------

* **Python-based**: Write build rules in readable Python instead of Make's syntax
* **Flexible**: Handle files, S3 objects, APIs, and any custom resources
* **Modern**: Built-in watch mode, parallel execution, and virtual environment support
* **Extensible**: Leverage Python's entire ecosystem in your build process

Quick Example
-------------

.. code-block:: python

    # Prodfile.py
    from pyprod import rule, task, run

    @rule("app", depends=["main.o", "utils.o"])
    def link(target, *objs):
        run("gcc", *objs, "-o", target)

    @rule("%.o", depends="%.c")
    def compile(target, source):
        run("gcc", "-c", source, "-o", target)

    @task
    def clean():
        run("rm", "-f", "*.o", "app")

Documentation Sections
----------------------

* `Getting Started <getting-started/installation.rst>`_ - Installation and first steps
* `Core Concepts <core-concepts/prodfile.rst>`_ - Understanding PyProd fundamentals
* `User Guide <user-guide/basic-usage.rst>`_ - Day-to-day usage patterns
* `Cookbook <cookbook/c-cpp-projects.rst>`_ - Solutions for specific scenarios
* `Advanced Topics <advanced/custom-checks.rst>`_ - Power user features
* `API Reference <reference/cli.rst>`_ - Complete API documentation
* `Migration Guides <migration/from-make.rst>`_ - Switching from other build tools

Getting Help
------------

* **GitHub Issues**: `Report bugs or request features <https://github.com/atsuoishimoto/pyprod/issues>`_
* **Documentation**: `Online docs <https://pyprod.readthedocs.io/>`_
* **Examples**: Check the ``samples/`` directory in the repository

.. toctree::
   :maxdepth: 2
   :hidden:

   getting-started/index
   core-concepts/index
   user-guide/index
   cookbook/index
   advanced/index
   reference/index
   migration/index
   contributing/index