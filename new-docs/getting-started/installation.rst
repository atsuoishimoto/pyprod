Installation
============

This guide covers how to install PyProd on various platforms and set up your environment
for productive use.

Requirements
------------

PyProd requires:

* Python 3.10 or higher
* pip (Python package installer)

Optional but recommended:

* `uv <https://github.com/astral-sh/uv>`_ - Fast Python package installer
* Git (for development installation)

Quick Install
-------------

Using pip
~~~~~~~~~

The simplest way to install PyProd is using pip:

.. code-block:: bash

    pip install pyprod

Using uv
~~~~~~~~

For faster installation, you can use uv:

.. code-block:: bash

    uv pip install pyprod

Verify Installation
~~~~~~~~~~~~~~~~~~~

After installation, verify PyProd is working:

.. code-block:: bash

    pyprod --version

Development Installation
------------------------

If you want to contribute to PyProd or use the latest development version:

Clone the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    git clone https://github.com/atsuoishimoto/pyprod.git
    cd pyprod

Install with uv (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Install PyProd and all development dependencies
    uv sync --dev
    
    # Or install in editable mode
    uv pip install -e .

Install with pip
~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Install in editable mode
    pip install -e .
    
    # Install development dependencies
    pip install -e ".[dev]"

Platform-Specific Notes
-----------------------

Linux
~~~~~

PyProd works out of the box on most Linux distributions. Ensure you have Python 3.10+:

.. code-block:: bash

    python3 --version

macOS
~~~~~

On macOS, you might need to use ``python3`` instead of ``python``:

.. code-block:: bash

    python3 -m pip install pyprod

If you're using Homebrew, you can ensure you have the latest Python:

.. code-block:: bash

    brew install python@3.11

Windows
~~~~~~~

PyProd fully supports Windows. Install using:

.. code-block:: bash

    py -m pip install pyprod

For development on Windows with WSL:

.. code-block:: bash

    # In WSL terminal
    pip install pyprod

Virtual Environments
--------------------

It's recommended to install PyProd in a virtual environment:

Using venv
~~~~~~~~~~

.. code-block:: bash

    # Create virtual environment
    python -m venv pyprod-env
    
    # Activate it
    # On Linux/macOS:
    source pyprod-env/bin/activate
    # On Windows:
    pyprod-env\Scripts\activate
    
    # Install PyProd
    pip install pyprod

Using uv
~~~~~~~~

uv automatically manages virtual environments:

.. code-block:: bash

    # Create a new project with PyProd
    uv init my-project
    cd my-project
    uv add pyprod

Docker Installation
-------------------

You can also use PyProd in a Docker container:

.. code-block:: dockerfile

    FROM python:3.11-slim
    
    RUN pip install pyprod
    
    WORKDIR /app
    COPY . .
    
    CMD ["pyprod"]

Build and run:

.. code-block:: bash

    docker build -t my-pyprod-app .
    docker run -v $(pwd):/app my-pyprod-app pyprod build

Troubleshooting
---------------

Permission Errors
~~~~~~~~~~~~~~~~~

If you encounter permission errors, use the ``--user`` flag:

.. code-block:: bash

    pip install --user pyprod

Or use a virtual environment (recommended).

Import Errors
~~~~~~~~~~~~~

If PyProd commands aren't found after installation:

1. Ensure your Python scripts directory is in PATH
2. Try using the module directly:

   .. code-block:: bash

       python -m pyprod --version

Dependency Conflicts
~~~~~~~~~~~~~~~~~~~~

If you have dependency conflicts, create a fresh virtual environment:

.. code-block:: bash

    python -m venv fresh-env
    source fresh-env/bin/activate  # or fresh-env\Scripts\activate on Windows
    pip install pyprod

Next Steps
----------

Once PyProd is installed, you can:

* Continue to the :doc:`quickstart` guide
* Read about :doc:`../core-concepts/prodfile` to understand the basics
* Check out the :doc:`first-project` tutorial

Getting Help
------------

If you encounter issues:

* Check the `GitHub Issues <https://github.com/atsuoishimoto/pyprod/issues>`_
* See the :doc:`../user-guide/debugging` guide
* Ask questions on the `Discussions <https://github.com/atsuoishimoto/pyprod/discussions>`_ page