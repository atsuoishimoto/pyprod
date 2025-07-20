Your First Project
==================

Learn how to set up a complete PyProd project from scratch. We'll build a simple
static site generator that converts Markdown files to HTML, demonstrating PyProd's
key features along the way.

Project Overview
----------------

We'll create a static site generator with these features:

* Convert Markdown files to HTML
* Apply a template to all pages
* Generate a sitemap
* Copy images alongside content
* Watch for changes and auto-rebuild

This project will showcase:

- File pattern rules
- Multiple dependencies
- Automatic package installation with pip()
- Order-only dependencies with uses
- Custom Python logic
- Parallel builds
- Watch mode

Project Structure
-----------------

Let's start by creating our project directory:

.. code-block:: bash

    mkdir my-site
    cd my-site
    
    # Create directories
    mkdir -p src templates

    # Create some sample files
    echo "# Welcome" > src/index.md
    echo "# About Us" > src/about.md
    echo "<html><body>{{ content }}</body></html>" > templates/base.html
    
    # Add an image to src directory
    # (In real project, add your .jpg files to src/)

Creating the Prodfile
---------------------

Create a ``Prodfile.py`` in your project root:

.. code-block:: python

    # Prodfile.py
    import os
    from pathlib import Path
    from pyprod import rule, task, run, glob, pip

    # Auto-install required packages
    # PyProd will automatically install 'markdown' if it's not already installed
    pip("markdown")
    import markdown

    # Configuration
    SRC_DIR = "src"
    BUILD_DIR = "build"
    TEMPLATE = "templates/base.html"

    # Rule to create the build directory
    @rule(BUILD_DIR)
    def create_build_dir(target):
        """Create the build directory"""
        os.makedirs(target, exist_ok=True)

    @rule("build/%.html", depends=["src/%.md", TEMPLATE], uses=BUILD_DIR)
    def markdown_to_html(target, source, template):
        """Convert Markdown files to HTML"""
        # Read markdown
        with open(source, 'r') as f:
            md_content = f.read()
        
        # Convert to HTML
        html_content = markdown.markdown(md_content)
        
        # Apply template
        with open(template, 'r') as f:
            template_content = f.read()
        
        final_html = template_content.replace("{{ content }}", html_content)
        
        # Write output
        with open(target, 'w') as f:
            f.write(final_html)
        
        print(f"✓ Generated {target}")

    @rule("build/%.jpg", depends="src/%.jpg", uses=BUILD_DIR)
    def copy_image(target, source):
        """Copy images to build directory"""
        # For now, just copy. In real project, use Pillow to optimize
        run("cp", source, target)
        print(f"✓ Copied {target}")

    @task
    def sitemap():
        """Generate sitemap.xml"""
        html_files = glob("build/*.html")
        with open("build/sitemap.xml", 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for html in html_files:
                url = html.replace('build/', 'https://example.com/')
                f.write(f'  <url><loc>{url}</loc></url>\n')
            f.write('</urlset>')
        print("✓ Generated sitemap.xml")

    @task(default=True)
    def build():
        """Build all pages and assets"""
        # Find all markdown files
        md_files = glob("src/*.md")
        html_files = [f.replace('src/', 'build/').replace('.md', '.html') 
                      for f in md_files]
        
        # Find all images
        images = glob("src/*.jpg")
        copied_images = [f.replace('src/', 'build/') for f in images]
        
        # Build everything
        targets = html_files + copied_images
        if targets:
            run("pyprod", *targets)
        
        # Generate sitemap after HTML files are built
        run("pyprod", "sitemap")

    @task
    def clean():
        """Remove all generated files"""
        run("rm", "-rf", BUILD_DIR)
        print("✓ Cleaned build directory")

    @task
    def serve():
        """Start development server"""
        print("Starting server at http://localhost:8000")
        run("python", "-m", "http.server", "8000", "--directory", BUILD_DIR)

Understanding the 'uses' Parameter
----------------------------------

Notice the ``uses`` parameter in our rules? This is PyProd's equivalent of Make's
"order-only prerequisites". It specifies dependencies that must exist but whose
timestamps don't trigger rebuilds:

.. code-block:: python

    # Define a rule to create the build directory
    @rule(BUILD_DIR)
    def create_build_dir(target):
        os.makedirs(target, exist_ok=True)

    # Use BUILD_DIR as an order-only dependency
    @rule("build/%.html", depends=["src/pages/%.md", TEMPLATE], uses=BUILD_DIR)
    def markdown_to_html(target, source, template):
        # BUILD_DIR will be created if it doesn't exist
        # But changes to BUILD_DIR timestamp won't trigger rebuilds

The ``uses`` parameter:

- Specifies dependencies that must exist before the rule runs
- Does NOT trigger rebuilds when these dependencies change
- Perfect for directories, tools, or other prerequisites
- Equivalent to Make's order-only prerequisites (target: deps | order-only)

Key difference from ``depends``:

.. code-block:: python

    # depends: Rebuilds if template.html is newer than output
    @rule("output.html", depends="template.html")
    
    # uses: Ensures build/ exists but doesn't rebuild if build/ is touched
    @rule("output.html", depends="input.md", uses="build/")

Running Your First Build
------------------------

Now let's build the site:

.. code-block:: bash

    # Build everything (runs the default task)
    $ pyprod
    ✓ Generated build/index.html
    ✓ Generated build/about.html
    ✓ Generated sitemap.xml

    # Check what was created
    $ ls build/
    about.html  index.html  sitemap.xml

    # View the generated HTML
    $ cat build/index.html
    <html><body><h1>Welcome</h1></body></html>

Understanding Dependencies
--------------------------

PyProd tracks dependencies intelligently. Try this:

.. code-block:: bash

    # Run build again - nothing happens!
    $ pyprod
    build/index.html: up to date
    build/about.html: up to date

    # Modify a source file
    $ echo "# Welcome to My Site" > src/index.md

    # PyProd knows what needs rebuilding
    $ pyprod
    ✓ Generated build/index.html

    # Change the template - all HTML files rebuild
    $ echo "<html><head><title>My Site</title></head><body>{{ content }}</body></html>" > templates/base.html
    $ pyprod
    ✓ Generated build/index.html
    ✓ Generated build/about.html

Using Watch Mode
----------------

PyProd can automatically rebuild when files change:

.. code-block:: bash

    # In one terminal, start watch mode
    $ pyprod -w src build
    Watching for changes... Press Ctrl+C to stop

    # In another terminal, start the server
    $ pyprod serve
    Starting server at http://localhost:8000

Now edit any markdown file or template, and PyProd will automatically rebuild!

Parallel Builds
---------------

For larger projects, use parallel execution:

.. code-block:: bash

    # Build with 4 parallel jobs
    $ pyprod -j 4 build

    # Or use all available CPU cores
    $ pyprod -j build

Adding More Features
--------------------

Let's extend our Prodfile with more capabilities:

.. code-block:: python

    @rule("build/%.css", depends="src/styles/%.scss")
    def compile_sass(target, source):
        """Compile SCSS to CSS"""
        run("sass", source, target)

    @task
    def deploy():
        """Deploy to production"""
        run("pyprod", "build")  # Ensure everything is built
        run("rsync", "-avz", "--delete", 
            f"{BUILD_DIR}/", "user@server:/var/www/html/")
        print("✓ Deployed to production")

    @check("https://api.github.com/repos/myuser/myrepo")
    def check_github_api(resource):
        """Check if repo data has changed"""
        import requests
        response = requests.get(resource)
        # Return timestamp or hash for change detection
        return response.headers.get('Last-Modified')

    @rule("build/data/repo.json", depends="https://api.github.com/repos/myuser/myrepo")
    def fetch_repo_data(target, source):
        """Fetch latest repo data"""
        import requests
        response = requests.get(source)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'w') as f:
            f.write(response.text)

Best Practices
--------------

1. **Organize your Prodfile**: For larger projects, split into multiple files:

   .. code-block:: python

       # Prodfile.py
       from build_rules import *
       from deploy_tasks import *

2. **Use variables for paths**: Makes maintenance easier:

   .. code-block:: python

       SOURCES = glob("src/**/*.md")
       TARGETS = [s.replace('src/', 'build/').replace('.md', '.html') 
                  for s in SOURCES]

3. **Add progress indicators**: Helpful for long builds:

   .. code-block:: python

       @rule("%.min.js", depends="%.js")
       def minify_js(target, source):
           print(f"Minifying {source}...")
           run("terser", source, "-o", target)
           size_before = os.path.getsize(source)
           size_after = os.path.getsize(target)
           print(f"✓ Reduced by {(1 - size_after/size_before) * 100:.1f}%")

Complete Example
----------------

Here's the complete Prodfile for reference:

.. code-block:: python

    # Complete Prodfile.py
    import os
    from pathlib import Path
    from pyprod import rule, task, run, glob, check, pip

    # Auto-install dependencies
    pip("markdown")
    import markdown

    # Configuration
    SRC_DIR = "src"
    BUILD_DIR = "build"
    TEMPLATE = "templates/base.html"

    # Rule to create build directory
    @rule(BUILD_DIR)
    def create_build_dir(target):
        os.makedirs(target, exist_ok=True)

    # All other rules and tasks from above, using 'uses' parameter
    # for order-only dependencies

    # Additional utility tasks
    @task
    def stats():
        """Show build statistics"""
        html_files = glob("build/*.html")
        total_size = sum(os.path.getsize(f) for f in html_files)
        print(f"Built {len(html_files)} HTML files")
        print(f"Total size: {total_size / 1024:.1f} KB")

    @task
    def validate():
        """Validate HTML output"""
        html_files = glob("build/*.html")
        for html in html_files:
            run("html-validate", html)

Next Steps
----------

Congratulations! You've built your first PyProd project. You've learned:

- Creating rules with pattern matching
- Managing multiple dependencies
- Using Python logic in build rules
- Running parallel builds
- Using watch mode for development

To learn more:

* Explore :doc:`../core-concepts/rules` for advanced pattern matching
* Read about :doc:`../core-concepts/checks` for custom dependency checking
* See :doc:`../cookbook/python-projects` for Python-specific workflows
* Check :doc:`../user-guide/best-practices` for larger projects

Happy building with PyProd!