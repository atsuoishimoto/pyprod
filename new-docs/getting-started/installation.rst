Installation
============

This guide covers how to install PyProd on your system.

Recommended Installation with uv
--------------------------------

We recommend using `uv <https://github.com/astral-sh/uv>`_ for the best experience. uv is an extremely fast Python package installer and resolver.

Install uv
~~~~~~~~~~

First, install uv:

.. code-block:: bash

    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

Install PyProd
~~~~~~~~~~~~~~

Then, use ``uv tool install`` to make the ``pyprod`` command available globally without polluting your system's Python environment:

.. code-block:: bash

    uv tool install pyprod

This is the cleanest and fastest way to install PyProd.

Verify Installation
~~~~~~~~~~~~~~~~~~~

After installation, verify PyProd is working:

.. code-block:: bash

    pyprod --version

Alternative Installation Methods
--------------------------------

Using pip
~~~~~~~~~

If you prefer traditional pip:

.. code-block:: bash

    pip install pyprod

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For contributing to PyProd:

.. code-block:: bash

    git clone https://github.com/atsuoishimoto/pyprod.git
    cd pyprod
    uv sync --dev

Requirements
------------

* Python 3.10 or higher

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