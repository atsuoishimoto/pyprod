Quick Start
===========

Get started with PyProd in 5 minutes! This guide will walk you through creating
your first Prodfile and running basic build tasks.

Prerequisites
-------------

Make sure you have PyProd installed:

.. code-block:: bash

    pyprod --version

If not, follow the :doc:`installation` guide.

Your First Prodfile
-------------------

PyProd uses a ``Prodfile.py`` instead of a ``Makefile``. Create one in your project directory:

.. code-block:: python

    # Prodfile.py
    from pyprod import task, rule, run

    @task
    def hello():
        """Say hello to PyProd!"""
        print("Hello from PyProd!")
        print("This is much nicer than Make, isn't it?")

    @task
    def clean():
        """Clean up generated files"""
        run("rm", "-f", "*.o", "*.tmp", "output.txt")

Run your first task:

.. code-block:: bash

    $ pyprod hello
    Hello from PyProd!
    This is much nicer than Make, isn't it?

Building Files with Rules
-------------------------

Let's create a more realistic example that transforms files:

.. code-block:: python

    # Prodfile.py
    from pyprod import task, rule, run

    @rule("output.txt", depends="input.txt")
    def process_file(target, source):
        """Transform input.txt to output.txt"""
        with open(source, 'r') as f:
            content = f.read().upper()
        
        with open(target, 'w') as f:
            f.write(f"PROCESSED:\n{content}")
        
        print(f"Created {target} from {source}")

    @task
    def prepare():
        """Create sample input file"""
        with open("input.txt", 'w') as f:
            f.write("hello world from pyprod!")

Try it out:

.. code-block:: bash

    # Create the input file
    $ pyprod prepare

    # Build output.txt (PyProd will detect the dependency)
    $ pyprod output.txt
    Created output.txt from input.txt

    # Run it again - PyProd knows it's up to date!
    $ pyprod output.txt
    output.txt: up to date

Pattern Rules for Multiple Files
--------------------------------

PyProd supports pattern rules, just like Make but with Python syntax:

.. code-block:: python

    # Prodfile.py
    from pyprod import rule, task, run, glob

    @rule("%.upper", depends="%.txt")
    def uppercase_file(target, source):
        """Convert any .txt file to .upper"""
        with open(source, 'r') as f:
            content = f.read().upper()
        with open(target, 'w') as f:
            f.write(content)
        print(f"Converted {source} -> {target}")

    @task
    def all():
        """Build all .upper files from .txt files"""
        txt_files = glob("*.txt")
        upper_files = [f.replace('.txt', '.upper') for f in txt_files]
        run(f"pyprod {' '.join(upper_files)}")

Create some test files and run:

.. code-block:: bash

    $ echo "hello" > file1.txt
    $ echo "world" > file2.txt
    $ pyprod file1.upper
    Converted file1.txt -> file1.upper
    $ pyprod file2.upper
    Converted file2.txt -> file2.upper

Using Shell Commands
--------------------

PyProd makes it easy to run shell commands with the ``run()`` function:

.. code-block:: python

    # Prodfile.py
    from pyprod import task, rule, run

    @task
    def test():
        """Run tests"""
        run("python", "-m", "pytest", "-v")

    @task
    def format():
        """Format code with black"""
        run("black", ".")

    @task
    def lint():
        """Check code with ruff"""
        run("ruff", "check", ".")

    @rule("dist/app.tar.gz", depends=glob("src/**/*.py"))
    def package(target, *sources):
        """Create distribution package"""
        run("mkdir", "-p", "dist")
        run("tar", "-czf", target, "src/")
        print(f"Package created: {target}")

Key Concepts Learned
--------------------

In this quickstart, you've learned:

1. **Tasks** (``@task``): Standalone operations like ``clean`` or ``test``
2. **Rules** (``@rule``): File transformations with automatic dependency tracking
3. **Pattern Rules**: Transform multiple files with patterns like ``%.o`` from ``%.c``
4. **Shell Commands**: Use ``run()`` to execute any shell command
5. **Dependency Tracking**: PyProd automatically knows when files need rebuilding

Default Task
------------

You can set a default task that runs when no target is specified:

.. code-block:: python

    # Prodfile.py
    from pyprod import task, set_default

    @task
    def build():
        """Default build task"""
        print("Building project...")
        # Your build logic here

    # Set as default
    set_default("build")

Now just running ``pyprod`` will execute the build task.

Next Steps
----------

You've completed the quickstart! Here's what to explore next:

* :doc:`first-project` - Build a complete project
* :doc:`../core-concepts/prodfile` - Deep dive into Prodfile structure
* :doc:`../core-concepts/rules` - Advanced rule patterns
* :doc:`../user-guide/watch-mode` - Auto-rebuild on file changes

Tips
----

* Run ``pyprod -h`` to see all available options
* Use ``pyprod -v`` for verbose output during builds
* Add ``-j 4`` to run up to 4 tasks in parallel
* List all tasks with ``pyprod -l``