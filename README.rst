PyProd: A Python-Native Workflow Engine for Any Resource
=========================================================

**PyProd is a modern workflow automation engine that uses Python to orchestrate complex tasks, going far beyond the limitations of traditional, file-based build tools like Make.**

While PyProd can replace Makefiles and shell scripts, its true power lies in its ability to treat **any resource**—not just files—as a dependency. With the `@check` decorator, you can define custom logic to check the state of database records, S3 objects, API endpoints, or any other resource you can query with Python. 

This transforms PyProd from a simple build tool into a flexible and powerful engine for orchestrating sophisticated, real-world workflows.

For detailed documentation, please refer to the `official documentation <https://pyprod.readthedocs.io/en/stable/>`_.

Beyond Files: The Power of `@check`
-----------------------------------

The `@check` decorator is what sets PyProd apart. While `make` is limited to checking file timestamps, `@check` lets you define a dependency with a custom Python function. This function returns a timestamp, a hash, or any value representing the state of a resource. PyProd will only run the tasks that depend on it if this value changes.

This unlocks a new level of automation possibilities:

*   **Database-Driven Workflows:** Trigger a task only when a specific record in your database is updated.

    .. code-block:: python

        @check("db://users/latest")
        def check_latest_user(target):
            return db.get_latest_user_timestamp()

        @rule("report.pdf", depends="db://users/latest")
        def generate_report(target, deps):
            # This runs only when a new user is added
            create_report()

*   **Cloud & API Integration:** Depend on the state of cloud resources. For example, run a task only if an object in an S3 bucket has been modified.

    .. code-block:: python

        import boto3

        @check("s3://my-bucket/data.csv")
        def check_s3_object(target):
            s3 = boto3.client("s3")
            response = s3.head_object(Bucket="my-bucket", Key="data.csv")
            return response["LastModified"]

*   **And More:** Check the latest Git commit, the response of a web API, or any other stateful resource you can imagine.

Core Philosophy
---------------

*   **Python as the DSL:** Use pure Python to define tasks, giving you access to its rich standard library and the entire PyPI ecosystem.
*   **Abstract Dependency-Aware Execution:** Intelligently skips tasks when the state of any dependent resource (file, database record, S3 object, etc.) hasn't changed.
*   **Modern Development Features:** Includes built-in support for **automatic virtual environment management**, a **file watcher for auto-rebuilds** (`--watch`), and **Git-aware timestamp checking** (`-g`).

Installation
------------
To install PyProd, simply use pip:

.. code-block:: sh

    pip install pyprod

Explore More
------------
You can find concrete examples, including **S3 file management** and documentation generation, in the `samples <https://github.com/atsuoishimoto/pyprod/tree/main/samples>`_ directory. These examples showcase the true power and versatility of PyProd beyond simple file-based tasks.

License
-------
PyProd is licensed under the MIT License. See the `LICENSE <LICENSE>`_ file for more details.