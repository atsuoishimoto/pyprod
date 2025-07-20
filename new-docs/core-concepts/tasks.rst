Tasks
=====

Tasks are standalone operations in PyProd that don't produce files. They're perfect
for actions like cleaning, testing, deploying, or any operation that doesn't fit
the source-to-target pattern of rules.

Basic Task Syntax
-----------------

A task is a Python function decorated with ``@task``:

.. code-block:: python

    from pyprod import task, run

    @task
    def clean():
        """Remove build artifacts"""
        run("rm", "-rf", "build/", "*.pyc", "__pycache__")

    @task
    def test():
        """Run test suite"""
        run("pytest", "-v")

Key differences from rules:

- No target file to build
- No dependency tracking
- Always runs when called (like Make's .PHONY targets)
- Can be set as the default task

Default Tasks
-------------

Mark a task as default to run when ``pyprod`` is called without arguments:

.. code-block:: python

    @task(default=True)
    def build():
        """Default build task"""
        print("Building project...")
        # Build logic here

    # Only one task can be default
    # If no default=True, the first defined target becomes default

Task Parameters
---------------

Tasks are regular Python functions, so they can accept parameters:

.. code-block:: python

    from pyprod import params

    @task
    def deploy():
        """Deploy to specified environment"""
        env = params.get("ENV", "staging")
        
        if env == "production":
            print("⚠️  Deploying to PRODUCTION!")
            response = input("Are you sure? (yes/no): ")
            if response != "yes":
                return
        
        run("rsync", "-av", "build/", f"{env}:/var/www/")

Call with: ``pyprod deploy -D ENV=production``

Using the build() Function
--------------------------

Tasks often need to build other targets. Use ``build()`` to schedule targets for building:

.. code-block:: python

    from pyprod import build

    @task(default=True)
    def all():
        """Build everything"""
        # Schedule specific targets to be built
        build("app.exe", "docs/manual.pdf")
        
        # Schedule lists of targets
        build(HTML_FILES, CSS_FILES)
        
        # Schedule other tasks
        build("test")
        
        # Note: build() only schedules - execution happens after the task returns

    @task
    def release():
        """Create a release"""
        # Schedule builds - these will execute AFTER this task completes
        build("all", "test")
        
        # This runs immediately, but might run before builds complete!
        # run("tar", "-czf", "release.tar.gz", "build/")
        
        # Better: Create a separate task or rule that depends on built files

Important: ``build()`` schedules targets but doesn't execute them immediately. The actual building happens after your task function returns. If you need to ensure targets are built before proceeding, create separate tasks or use rules with proper dependencies.

Common Task Patterns
--------------------

Cleaning Tasks
~~~~~~~~~~~~~~

.. code-block:: python

    import shutil
    from pathlib import Path

    @task
    def clean():
        """Remove all generated files"""
        # Cross-platform cleaning
        shutil.rmtree("build", ignore_errors=True)
        shutil.rmtree("dist", ignore_errors=True)
        
        # Remove specific patterns
        for pattern in ["*.pyc", "*.pyo", "*.so", "*.o"]:
            for file in Path(".").rglob(pattern):
                file.unlink()

    @task
    def distclean():
        """Clean everything including downloads"""
        build("clean")  # Run clean task first
        shutil.rmtree(".venv", ignore_errors=True)
        shutil.rmtree("downloads", ignore_errors=True)

Testing Tasks
~~~~~~~~~~~~~

.. code-block:: python

    @task
    def test():
        """Run unit tests"""
        run("pytest", "tests/")

    @task
    def test_integration():
        """Run integration tests"""
        run("pytest", "tests/integration/", "-m", "integration")

    @task
    def coverage():
        """Run tests with coverage"""
        run("pytest", "--cov=src", "--cov-report=html")
        print("Coverage report: htmlcov/index.html")

    @task
    def lint():
        """Check code quality"""
        run("ruff", "check", "src/", "tests/")
        run("mypy", "src/")

Development Tasks
~~~~~~~~~~~~~~~~~

.. code-block:: python

    @task
    def serve():
        """Start development server"""
        import subprocess
        
        # Start in background
        server = subprocess.Popen(
            ["python", "-m", "http.server", "8000"],
            cwd="build"
        )
        
        print("Server running at http://localhost:8000")
        print("Press Ctrl+C to stop")
        
        try:
            server.wait()
        except KeyboardInterrupt:
            server.terminate()

    @task
    def watch():
        """Watch for changes and rebuild"""
        # PyProd has built-in watch mode
        run("pyprod", "-w", "src", "all")

Deployment Tasks
~~~~~~~~~~~~~~~~

.. code-block:: python

    @task
    def deploy():
        """Deploy to production"""
        # Check prerequisites
        if not Path("build").exists():
            print("Error: No build directory. Run 'pyprod all' first.")
            return
        
        # Run tests first (immediate execution)
        try:
            run("pytest", "--tb=short")
        except Exception:
            print("Tests failed! Aborting deployment.")
            return
        
        # Deploy (immediate execution)
        run("rsync", "-avz", "--delete", 
            "build/", "user@prod:/var/www/html/")
        
        # Notify
        run("curl", "-X", "POST", 
            "https://api.slack.com/notify",
            "-d", "Deployment complete")
    
    # Better pattern: Use a rule for deployment that depends on built files
    @rule("deployed.flag", depends=["app.exe", "tests.passed"])
    def deploy_rule(target, app, tests):
        """Deploy only after build and tests succeed"""
        run("rsync", "-avz", "--delete", "build/", "user@prod:/var/www/html/")
        Path(target).touch()  # Create flag file

Task Organization
-----------------

Group Related Tasks
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # === Build Tasks ===
    
    @task(default=True)
    def build_all():
        """Build the project"""
        # Schedule executables and libraries to be built
        build(EXECUTABLES, LIBRARIES)
    
    @task
    def rebuild():
        """Clean and build"""
        # Note: clean will run first, then build_all
        # Both are scheduled, execution happens after task returns
        build("clean", "build_all")
    
    # === Test Tasks ===
    
    @task
    def test():
        """Run all tests"""
        build("test_unit", "test_integration")
    
    @task
    def test_unit():
        """Run unit tests only"""
        run("pytest", "tests/unit/")
    
    # === Release Tasks ===
    
    @task
    def release():
        """Create release package"""
        build("test", "build", "package")

Task Composition
~~~~~~~~~~~~~~~~

Tasks can call other tasks programmatically:

.. code-block:: python

    def run_checks():
        """Helper function for common checks"""
        run("ruff", "check", ".")
        run("mypy", ".")
        run("pytest", "--tb=short")

    @task
    def ci():
        """Run continuous integration checks"""
        run_checks()
        run("coverage", "report", "--fail-under=80")

    @task
    def pre_commit():
        """Pre-commit checks"""
        run_checks()
        print("✅ All checks passed!")

Error Handling
--------------

Tasks should handle errors appropriately:

.. code-block:: python

    @task
    def validate():
        """Validate project configuration"""
        errors = []
        
        # Check required files
        for required in ["README.md", "LICENSE", "pyproject.toml"]:
            if not Path(required).exists():
                errors.append(f"Missing {required}")
        
        # Check version
        import toml
        try:
            config = toml.load("pyproject.toml")
            version = config["project"]["version"]
        except Exception as e:
            errors.append(f"Invalid pyproject.toml: {e}")
        
        if errors:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            raise SystemExit(1)
        
        print("✅ Validation passed!")

Interactive Tasks
-----------------

Tasks can interact with users:

.. code-block:: python

    @task
    def init():
        """Initialize a new project"""
        import questionary
        
        # Use questionary for nice prompts (pip("questionary") first)
        pip("questionary")
        import questionary
        
        project_name = questionary.text("Project name:").ask()
        project_type = questionary.select(
            "Project type:",
            choices=["library", "application", "website"]
        ).ask()
        
        # Create structure based on answers
        Path(project_name).mkdir()
        # ... create files based on project_type ...

Task Discovery
--------------

List all available tasks:

.. code-block:: bash

    $ pyprod -l
    Available tasks:
      all         Build everything (default)
      clean       Remove build artifacts
      test        Run test suite
      deploy      Deploy to production

Add descriptions to make tasks discoverable:

.. code-block:: python

    @task
    def secret_task():
        """[INTERNAL] Don't show in help"""
        # Tasks with [INTERNAL] in docstring can be hidden
        pass

Best Practices
--------------

1. **Use Descriptive Names**: Task names should be verbs that describe actions
2. **Add Docstrings**: Help users understand what each task does
3. **Handle Errors**: Don't let tasks fail silently
4. **Be Idempotent**: Running a task twice should be safe
5. **Show Progress**: Give feedback for long-running tasks

.. code-block:: python

    @task
    def download_data():
        """Download required data files"""
        import urllib.request
        
        files = [
            ("https://example.com/data1.csv", "data/data1.csv"),
            ("https://example.com/data2.csv", "data/data2.csv"),
        ]
        
        Path("data").mkdir(exist_ok=True)
        
        for url, dest in files:
            if Path(dest).exists():
                print(f"✓ {dest} already exists")
                continue
                
            print(f"⬇ Downloading {dest}...")
            urllib.request.urlretrieve(url, dest)
            print(f"✓ Downloaded {dest}")

Next Steps
----------

- Learn about :doc:`checks` for custom dependency types
- See :doc:`dependencies` for complex dependency management
- Explore :doc:`../user-guide/best-practices` for task organization