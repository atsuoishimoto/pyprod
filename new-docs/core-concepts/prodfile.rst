The Prodfile
============

The Prodfile is the heart of your PyProd build system. It's a Python script that defines
your build rules, tasks, and dependencies - replacing traditional Makefiles with the
full power of Python.

Basic Structure
---------------

A Prodfile is simply a Python script named ``Prodfile.py`` in your project root:

.. code-block:: python

    # Prodfile.py
    from pyprod import rule, task, run

    @task(default=True)
    def build():
        """Default build task"""
        print("Building project...")

    @rule("output.txt", depends="input.txt")
    def process(target, source):
        """Transform input.txt to output.txt"""
        with open(source) as f:
            data = f.read().upper()
        with open(target, 'w') as f:
            f.write(data)

Key Concepts
------------

Import What You Need
~~~~~~~~~~~~~~~~~~~~

PyProd provides several key functions and decorators:

.. code-block:: python

    from pyprod import (
        rule,     # Define file transformation rules
        task,     # Define standalone tasks
        check,    # Custom dependency checking
        run,      # Execute shell commands
        glob,     # File pattern matching
        build,    # Programmatically build targets
        pip,      # Auto-install Python packages
        params,   # Access command-line parameters
    )

Rules vs Tasks
~~~~~~~~~~~~~~

**Rules** define how to build files from dependencies:

.. code-block:: python

    @rule("output.pdf", depends="input.md")
    def make_pdf(target, source):
        run("pandoc", source, "-o", target)

**Tasks** are standalone operations without file outputs:

.. code-block:: python

    @task
    def clean():
        run("rm", "-rf", "build/")

    @task
    def test():
        run("pytest")

Using Python's Power
--------------------

Since Prodfile is Python, you can use any Python feature:

Variables and Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pathlib import Path
    
    # Configuration
    SRC_DIR = Path("src")
    BUILD_DIR = Path("build")
    DEBUG = params.get("DEBUG", False)
    
    # Compiler settings
    CC = "gcc"
    CFLAGS = ["-Wall", "-O2"]
    if DEBUG:
        CFLAGS.append("-g")

Dynamic Target Discovery
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Find all source files
    SOURCES = glob(SRC_DIR / "*.c")
    OBJECTS = [(BUILD_DIR / f.with_suffix(".o").name) for f in SOURCES]
    
    # Define rules for all files at once
    @rule(OBJECTS, pattern=(BUILD_DIR / "%.o"), depends="src/%.c")
    def compile(target, source):
        run(CC, *CFLAGS, "-c", source, "-o", target)

Conditional Logic
~~~~~~~~~~~~~~~~~

.. code-block:: python

    import platform
    
    if platform.system() == "Windows":
        EXE_EXT = ".exe"
    else:
        EXE_EXT = ""
    
    @rule(f"app{EXE_EXT}", depends=OBJECTS)
    def link(target, *objects):
        run(CC, *objects, "-o", target)

External Libraries
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Auto-install and use any Python package
    pip("requests", "pyyaml")
    import requests
    import yaml
    
    @task
    def fetch_config():
        """Download build configuration"""
        response = requests.get("https://example.com/config.yaml")
        config = yaml.safe_load(response.text)
        
        # Use config to set build parameters
        for key, value in config.items():
            params[key] = value

Advanced Patterns
-----------------

Virtual Environment Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyProd automatically creates and manages virtual environments:

.. code-block:: python

    # This creates/activates a venv and installs packages
    pip("numpy", "pandas", "matplotlib")
    
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    
    @task
    def analyze():
        """Run data analysis"""
        data = pd.read_csv("data.csv")
        # ... analysis code ...

Parameter Handling
~~~~~~~~~~~~~~~~~~

Access command-line parameters and environment variables:

.. code-block:: python

    # Access with: pyprod -D VERSION=1.2.3
    VERSION = params.get("VERSION", "dev")
    
    # Environment variables
    import os
    API_KEY = os.environ.get("API_KEY", "")
    
    @rule("config.h")
    def make_config(target):
        with open(target, 'w') as f:
            f.write(f'#define VERSION "{VERSION}"\n')
            f.write(f'#define API_KEY "{API_KEY}"\n')


Next Steps
----------

- Learn about :doc:`rules` for file transformation patterns
- Explore :doc:`tasks` for standalone operations  
- Understand :doc:`dependencies` for complex builds
- See :doc:`checks` for custom dependency types