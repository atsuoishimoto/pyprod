Rules
=====

Rules are the core of PyProd's build system. They define how to transform source files
into target files, with automatic dependency tracking and intelligent rebuilding.

Basic Rule Syntax
-----------------

A rule defines how to build a target file from one or more source files:

.. code-block:: python

    @rule("output.txt", depends="input.txt")
    def process_file(target, source):
        """Transform input.txt to output.txt"""
        with open(source, 'r') as f:
            content = f.read()
        with open(target, 'w') as f:
            f.write(content.upper())

Key points:

- ``target``: The file to be created (first parameter)
- ``depends``: Source file(s) the target depends on
- Function parameters match the rule definition order

Multiple Dependencies
---------------------

Rules can depend on multiple files:

.. code-block:: python

    @rule("report.pdf", depends=["data.csv", "template.tex"])
    def generate_report(target, data_file, template_file):
        # Process data_file and template_file to create target
        pass

    # Dependencies can also be a tuple
    @rule("combined.txt", depends=("file1.txt", "file2.txt", "file3.txt"))
    def combine_files(target, *sources):
        with open(target, 'w') as out:
            for source in sources:
                with open(source) as f:
                    out.write(f.read())

Pattern Rules
-------------

Pattern rules use ``%`` as a wildcard to define transformations for multiple files:

.. code-block:: python

    @rule("%.o", depends="%.c")
    def compile_c(target, source):
        """Compile any .c file to .o"""
        run("gcc", "-c", source, "-o", target)

    @rule("%.min.js", depends="%.js")
    def minify_js(target, source):
        """Minify any .js file"""
        run("terser", source, "-o", target, "--compress")

The ``%`` matches the same string in both target and dependencies.

List-Based Rules
----------------

Define rules for multiple targets at once:

.. code-block:: python

    from pathlib import Path
    
    SRC_DIR = Path("src")
    BUILD_DIR = Path("build")
    
    # Find all markdown files
    MD_FILES = glob(SRC_DIR / "*.md")
    HTML_FILES = [(BUILD_DIR / f.with_suffix(".html").name) for f in MD_FILES]
    
    @rule(HTML_FILES, depends="src/%.md")
    def markdown_to_html(target, source):
        # This rule applies to ALL files in HTML_FILES
        run("pandoc", source, "-o", target)

Static Pattern Rules
--------------------

Use the ``pattern`` parameter for more precise dependency mapping:

.. code-block:: python

    # Without pattern: unclear which source maps to which target
    @rule(HTML_FILES, depends="src/%.md")
    
    # With pattern: explicit mapping
    @rule(HTML_FILES, pattern=(BUILD_DIR / "%.html"), depends="src/%.md")
    def markdown_to_html(target, source):
        # Pattern extracts the stem from each target
        # build/index.html -> index -> src/index.md
        pass

This is equivalent to Make's static pattern rules:

.. code-block:: make

    $(HTML_FILES): build/%.html: src/%.md
        pandoc $< -o $@

Order-Only Dependencies (uses)
------------------------------

The ``uses`` parameter specifies prerequisites that must exist but don't trigger rebuilds:

.. code-block:: python

    @rule(BUILD_DIR)
    def create_build_dir(target):
        os.makedirs(target, exist_ok=True)
    
    @rule("build/output.txt", depends="input.txt", uses=BUILD_DIR)
    def process(target, source):
        # BUILD_DIR will be created if needed
        # But touching BUILD_DIR won't rebuild output.txt
        with open(source) as f:
            data = f.read()
        with open(target, 'w') as f:
            f.write(data)

This is like Make's order-only prerequisites:

.. code-block:: make

    build/output.txt: input.txt | build
        process $< > $@

Advanced Patterns
-----------------

Directory Patterns
~~~~~~~~~~~~~~~~~~

Match files in subdirectories:

.. code-block:: python

    @rule("build/%.html", depends="src/**/%.md")
    def deep_markdown(target, source):
        """Convert markdown from any subdirectory"""
        # src/docs/guide.md -> build/guide.html
        # src/blog/posts/hello.md -> build/hello.html
        pass

Multiple Pattern Rules
~~~~~~~~~~~~~~~~~~~~~~

Combine multiple patterns:

.. code-block:: python

    # Different source extensions
    @rule("%.o", depends=["%.c", "%.h"])
    def compile_with_header(target, source, header):
        run("gcc", "-c", source, "-o", target)
    
    # Multiple outputs from one source
    @rule(["%.o", "%.d"], depends="%.c")
    def compile_with_deps(obj_target, dep_target, source):
        run("gcc", "-c", source, "-o", obj_target, "-MMD", "-MF", dep_target)

Conditional Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

Use Python logic to determine dependencies:

.. code-block:: python

    def get_deps(target):
        """Dynamic dependency resolution"""
        base = Path(target).stem
        deps = [f"src/{base}.c"]
        
        # Add platform-specific dependencies
        if platform.system() == "Windows":
            deps.append(f"src/{base}_win.c")
        else:
            deps.append(f"src/{base}_unix.c")
        
        return deps
    
    @rule("%.o", depends=get_deps)
    def compile_platform(target, *sources):
        run("gcc", "-c", *sources, "-o", target)

Rule Execution
--------------

Dependency Resolution
~~~~~~~~~~~~~~~~~~~~~

PyProd automatically:

1. Checks if target exists
2. Compares timestamps of target vs dependencies
3. Rebuilds if any dependency is newer
4. Creates parent directories as needed

.. code-block:: python

    # PyProd handles all of this automatically
    @rule("deeply/nested/output.txt", depends="input.txt")
    def nested_output(target, source):
        # Parent directories are created automatically
        shutil.copy(source, target)

Parallel Execution
~~~~~~~~~~~~~~~~~~

Rules can run in parallel with ``-j``:

.. code-block:: bash

    # Run up to 4 rules simultaneously
    pyprod -j 4

Rules are parallelized when they have no interdependencies:

.. code-block:: python

    # These can run in parallel
    @rule("output1.txt", depends="input1.txt")
    def process1(target, source): pass
    
    @rule("output2.txt", depends="input2.txt")
    def process2(target, source): pass
    
    # This waits for both above
    @rule("combined.txt", depends=["output1.txt", "output2.txt"])
    def combine(target, *sources): pass

Error Handling
~~~~~~~~~~~~~~

Rules should handle errors gracefully:

.. code-block:: python

    @rule("%.pdf", depends="%.tex")
    def compile_latex(target, source):
        """Compile LaTeX with error handling"""
        try:
            run("pdflatex", source)
        except Exception as e:
            # Clean up partial output
            if Path(target).exists():
                Path(target).unlink()
            raise RuntimeError(f"LaTeX compilation failed: {e}")

Best Practices
--------------

1. **Use Descriptive Names**: Rule functions should describe what they do:

   .. code-block:: python

       # Good
       @rule("%.html", depends="%.md")
       def markdown_to_html(target, source): pass
       
       # Less clear
       @rule("%.html", depends="%.md")
       def process(target, source): pass

2. **Keep Rules Focused**: Each rule should do one thing:

   .. code-block:: python

       # Good: Separate rules for separate concerns
       @rule("%.o", depends="%.c")
       def compile(target, source):
           run("gcc", "-c", source, "-o", target)
       
       @rule("app", depends=glob("*.o"))
       def link(target, *objects):
           run("gcc", *objects, "-o", target)
       
       # Avoid: Doing too much in one rule
       @rule("app", depends=glob("*.c"))
       def build_all(target, *sources):
           # Compile and link in one rule - harder to parallelize
           pass

3. **Use Patterns for Consistency**: Pattern rules ensure uniform handling:

   .. code-block:: python

       # Define once, use for all files
       @rule("build/%.css", depends="src/%.scss")
       def compile_sass(target, source):
           run("sass", source, target, "--style=compressed")

4. **Document Complex Rules**: Add docstrings for non-obvious transformations:

   .. code-block:: python

       @rule("%.wasm", depends=["%.c", "%.wit"])
       def compile_wasm(target, source, interface):
           """Compile C to WebAssembly with WIT interface bindings
           
           Requires: wasi-sdk and wit-bindgen in PATH
           """
           # Complex compilation steps...

Common Patterns
---------------

Source to Object Files
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # C/C++ compilation
    C_SOURCES = glob("src/*.c")
    OBJECTS = [Path(f).with_suffix(".o").name for f in C_SOURCES]
    
    @rule(OBJECTS, pattern="%.o", depends="src/%.c", uses=".")
    def compile_c(target, source):
        run("gcc", "-c", source, "-o", target, "-O2", "-Wall")

Asset Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Image optimization
    IMAGES = glob("assets/*.png")
    OPTIMIZED = [f"build/{Path(f).name}" for f in IMAGES]
    
    @rule(OPTIMIZED, pattern="build/%", depends="assets/%")
    def optimize_image(target, source):
        run("optipng", "-o7", source, "-out", target)

Documentation Generation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # API docs from source
    @rule("docs/api.html", depends=glob("src/**/*.py"))
    def generate_api_docs(target, *sources):
        run("pdoc", "--html", "--output-dir", "docs", *sources)

Next Steps
----------

- Learn about :doc:`tasks` for standalone operations
- Understand :doc:`dependencies` for complex dependency graphs
- Explore :doc:`checks` for custom dependency types
- See :doc:`../user-guide/pattern-matching` for advanced patterns