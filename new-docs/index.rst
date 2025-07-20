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

* :doc:`Getting Started <getting-started/installation>` - Installation and first steps
* :doc:`Core Concepts <core-concepts/prodfile>` - Understanding PyProd fundamentals
* :doc:`User Guide <user-guide/basic-usage>` - Day-to-day usage patterns
* :doc:`Cookbook <cookbook/c-cpp-projects>` - Solutions for specific scenarios
* :doc:`Advanced Topics <advanced/custom-checks>` - Power user features
* :doc:`API Reference <reference/cli>` - Complete API documentation
* :doc:`Migration Guides <migration/from-make>` - Switching from other build tools

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