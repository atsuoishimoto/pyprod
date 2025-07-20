Quickstart
=============

This guide will help you get started with PyProd.

Installation
------------------

Install the package with pip:

.. code-block:: console

    pip install pyprod

PyProd currently support Python 3.10+.


Your first project
-----------------------

Create a new directory for your project and navigate to it:

.. code-block:: console

    mkdir myproject
    cd myproject

Create a new file called ``Prodfile.py``:

.. code-block:: python

    @rule("hello.txt")
    def hello(target):
        with open(target, "w") as f:
            f.write("Hello, world!")
    

The function ``hello`` is invoked when the target file is missing or outdated. In this case, the function writes the text ``Hello, world!`` to the file ``hello.txt``.

Run the build script:

.. code-block:: bash

    pyprod hello.txt

You should see a new file called ``hello.txt`` in your project directory with the content ``Hello, world!``.

Next steps
----------------

Next, let's modify the ``Prodfile.py`` to output the file into an ``output`` directory.

.. code-block:: python

   output = Path("output") # We can use pathlib.Path without importing it
   
   @rule(output / "hello.txt", depends=output) # hello now depends on output directory
   def hello(target):
       with open(target, "w") as f:
           f.write("Hello, world!")

   @rule(output)
   def makedir(target):
       os.makedirs(target)

In the modified ``Prodfile.py``, we have defined a rule to create the ``output`` directory and added a rule that makes the ``output/hello.txt`` file dependent on the ``output`` directory.

The build script will create the ``output`` directory if it doesn't exist and write the file ``hello.txt`` inside it.

Run the build script again:

.. code-block:: bash

    pyprod output/hello.txt

You should see a new file called ``hello.txt`` in the ``output`` directory with the content ``Hello, world!``.

Congratulations! You have successfully created a simple build script with PyProd. Continue exploring the documentation to learn more about defining rules, specifying dependencies, and extending the build logic with custom functions.
