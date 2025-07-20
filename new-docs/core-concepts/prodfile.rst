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

Multiple Prodfiles
~~~~~~~~~~~~~~~~~~

You can split large builds across multiple files:

.. code-block:: python

    # Prodfile.py
    from pathlib import Path
    
    # Import rules from subdirectories
    exec(open("src/Prodfile.py").read())
    exec(open("docs/Prodfile.py").read())
    exec(open("tests/Prodfile.py").read())

Or use Python's import system:

.. code-block:: python

    # Prodfile.py
    import sys
    sys.path.insert(0, '.')
    
    from build_rules.compilation import *
    from build_rules.packaging import *
    from build_rules.deployment import *

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

Error Handling
~~~~~~~~~~~~~~

Use Python's exception handling for robust builds:

.. code-block:: python

    @task
    def deploy():
        """Deploy with error checking"""
        try:
            run("ssh", "server", "test", "-f", "/app/health")
        except Exception as e:
            print(f"Health check failed: {e}")
            return
        
        # Only deploy if health check passed
        run("rsync", "-av", "build/", "server:/app/")

Best Practices
--------------

1. **Keep it Simple**: Start with basic rules and tasks, add complexity as needed.

2. **Use Path Objects**: Prefer ``pathlib.Path`` over string manipulation:

   .. code-block:: python

       # Good
       BUILD_DIR = Path("build")
       output = BUILD_DIR / "output.txt"
       
       # Less ideal
       output = "build/output.txt"

3. **Document Your Rules**: Use docstrings to explain what each rule does:

   .. code-block:: python

       @rule("%.min.js", depends="%.js")
       def minify(target, source):
           """Minify JavaScript files using terser"""
           run("terser", source, "-o", target, "--compress", "--mangle")

4. **Group Related Rules**: Organize your Prodfile logically:

   .. code-block:: python

       # === Compilation Rules ===
       
       @rule(OBJECTS, pattern=(BUILD_DIR / "%.o"), depends="src/%.c")
       def compile(target, source):
           # ...
       
       # === Testing Tasks ===
       
       @task
       def test():
           # ...
       
       @task  
       def coverage():
           # ...

5. **Use Default Tasks**: Mark your main build task as default:

   .. code-block:: python

       @task(default=True)
       def all():
           """Build everything"""
           build(EXECUTABLE, DOCS, TESTS)

Common Patterns
---------------

Development vs Production
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    MODE = params.get("MODE", "dev")
    
    if MODE == "production":
        OPTIMIZE = True
        MINIFY = True
        SOURCE_MAPS = False
    else:
        OPTIMIZE = False
        MINIFY = False
        SOURCE_MAPS = True

Cross-Platform Builds
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import platform
    import shutil
    
    # Platform-specific commands
    if platform.system() == "Windows":
        RM = ["cmd", "/c", "del", "/f", "/q"]
        MKDIR = ["cmd", "/c", "mkdir"]
    else:
        RM = ["rm", "-f"]
        MKDIR = ["mkdir", "-p"]
    
    # Or use Python's built-in functions
    @task
    def clean():
        """Cross-platform clean"""
        shutil.rmtree("build", ignore_errors=True)

Generated File Lists
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Generate file lists dynamically
    def get_test_files():
        """Find all test files"""
        return glob("tests/**/test_*.py")
    
    @task
    def test():
        """Run all tests"""
        test_files = get_test_files()
        if test_files:
            run("pytest", *test_files)

Next Steps
----------

- Learn about :doc:`rules` for file transformation patterns
- Explore :doc:`tasks` for standalone operations  
- Understand :doc:`dependencies` for complex builds
- See :doc:`checks` for custom dependency types