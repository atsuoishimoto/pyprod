Checks
======

Checks extend PyProd's dependency system beyond files. They let you define custom
logic to determine when targets need rebuilding based on any criteria - APIs,
databases, Git commits, or any state you can query with Python.

The @check Decorator
--------------------

The ``@check`` decorator defines how to check if a non-file dependency has changed:

.. code-block:: python

    from pyprod import check, rule

    @check("https://api.example.com/data")
    def check_api(resource):
        """Check API endpoint for changes"""
        import requests
        response = requests.head(resource)
        
        # Return something that changes when the resource changes
        return response.headers.get('ETag')

    @rule("data.json", depends="https://api.example.com/data")
    def fetch_data(target, source):
        """Fetch data when API changes"""
        import requests
        response = requests.get(source)
        with open(target, 'w') as f:
            f.write(response.text)

How Checks Work
---------------

1. PyProd calls your check function with the resource URL/path
2. Your function returns a value (timestamp, hash, version, etc.)
3. PyProd stores this value
4. On next build, it calls the check again
5. If the value changed, dependent rules are rebuilt

Return Values
~~~~~~~~~~~~~

Check functions should return:

- **Timestamps**: For time-based changes
- **Hashes**: For content-based changes
- **Version strings**: For versioned resources
- **Any comparable value**: That changes when the resource changes

.. code-block:: python

    import hashlib
    from datetime import datetime

    @check("s3://bucket/object")
    def check_s3_hash(resource):
        """Return MD5 hash of S3 object"""
        # ... boto3 code to get object ...
        return object_metadata['ETag']

    @check("git://HEAD")
    def check_git_commit(resource):
        """Return current Git commit hash"""
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        return result.stdout.strip()

Common Check Patterns
---------------------

S3 Objects
~~~~~~~~~~

.. code-block:: python

    pip("boto3")
    import boto3
    from urllib.parse import urlparse

    @check("s3://*")
    def check_s3_object(resource):
        """Check S3 object modification time"""
        parsed = urlparse(resource)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        s3 = boto3.client('s3')
        try:
            response = s3.head_object(Bucket=bucket, Key=key)
            return response['LastModified'].isoformat()
        except s3.exceptions.NoSuchKey:
            return None  # Object doesn't exist

    # Use in rules
    @rule("local/data.csv", depends="s3://my-bucket/data.csv")
    def download_from_s3(target, source):
        parsed = urlparse(source)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        s3 = boto3.client('s3')
        s3.download_file(bucket, key, target)

Database Records
~~~~~~~~~~~~~~~~

.. code-block:: python

    pip("psycopg2")
    import psycopg2
    from urllib.parse import urlparse

    @check("postgresql://*")
    def check_database_table(resource):
        """Check table modification time"""
        parsed = urlparse(resource)
        table = parsed.fragment  # postgresql://host/db#table
        
        conn = psycopg2.connect(resource.split('#')[0])
        cursor = conn.cursor()
        
        # Get table stats
        cursor.execute("""
            SELECT MAX(updated_at) 
            FROM pg_stat_user_tables 
            WHERE tablename = %s
        """, (table,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0].isoformat() if result[0] else None

    @rule("report.pdf", depends="postgresql://localhost/mydb#sales")
    def generate_report(target, source):
        # Generate report from database
        pass

Git Repositories
~~~~~~~~~~~~~~~~

.. code-block:: python

    import subprocess
    from pathlib import Path

    @check("git://*")
    def check_git_repo(resource):
        """Check Git repository state"""
        # Parse git://path/to/repo#branch
        parts = resource.replace("git://", "").split('#')
        repo_path = parts[0]
        branch = parts[1] if len(parts) > 1 else "HEAD"
        
        # Get latest commit hash
        result = subprocess.run(
            ["git", "rev-parse", branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        return result.stdout.strip()

    @rule("vendor/lib.zip", depends="git://./vendor/lib#main")
    def update_vendor(target, source):
        """Update vendored library when upstream changes"""
        repo_path = source.replace("git://", "").split('#')[0]
        run("git", "-C", repo_path, "pull")
        run("zip", "-r", target, repo_path)

HTTP Resources
~~~~~~~~~~~~~~

.. code-block:: python

    import requests
    from datetime import datetime

    @check("http://*", "https://*")
    def check_http_resource(resource):
        """Check HTTP resource modification"""
        response = requests.head(resource, allow_redirects=True)
        
        # Try different headers
        if 'ETag' in response.headers:
            return response.headers['ETag']
        elif 'Last-Modified' in response.headers:
            return response.headers['Last-Modified']
        else:
            # Fall back to content hash
            response = requests.get(resource)
            import hashlib
            return hashlib.md5(response.content).hexdigest()

    @rule("data/weather.json", depends="https://api.weather.com/current")
    def fetch_weather(target, source):
        response = requests.get(source)
        with open(target, 'w') as f:
            f.write(response.text)

Advanced Check Features
-----------------------

Pattern Matching
~~~~~~~~~~~~~~~~

Checks can use patterns like rules:

.. code-block:: python

    @check("docker://%")
    def check_docker_image(resource):
        """Check Docker image digest"""
        image = resource.replace("docker://", "")
        
        import subprocess
        result = subprocess.run(
            ["docker", "inspect", image, "--format", "{{.Id}}"],
            capture_output=True,
            text=True
        )
        
        return result.stdout.strip() if result.returncode == 0 else None

    @rule("app.tar", depends="docker://myapp:latest")
    def export_docker(target, source):
        image = source.replace("docker://", "")
        run("docker", "save", image, "-o", target)

Composite Checks
~~~~~~~~~~~~~~~~

Check multiple resources:

.. code-block:: python

    @check("config://*")
    def check_config(resource):
        """Check multiple config sources"""
        import hashlib
        
        # Combine multiple sources
        sources = [
            Path("config.yaml").stat().st_mtime if Path("config.yaml").exists() else 0,
            os.environ.get("CONFIG_VERSION", ""),
            requests.get("https://api.example.com/config/version").text
        ]
        
        # Return combined hash
        combined = "|".join(str(s) for s in sources)
        return hashlib.md5(combined.encode()).hexdigest()

Caching Checks
~~~~~~~~~~~~~~

For expensive checks, implement caching:

.. code-block:: python

    import time
    from functools import lru_cache

    # Cache for 60 seconds
    @lru_cache(maxsize=100)
    def _cached_api_check(resource, cache_time):
        """Actual API check"""
        response = requests.get(resource)
        return response.headers.get('X-Version')

    @check("api://*")
    def check_api_cached(resource):
        """Check API with caching"""
        # Round time to nearest minute for caching
        cache_time = int(time.time() / 60)
        return _cached_api_check(resource, cache_time)

Error Handling
--------------

Checks should handle failures gracefully:

.. code-block:: python

    @check("service://*")
    def check_service(resource):
        """Check service availability"""
        import socket
        
        service = resource.replace("service://", "")
        host, port = service.split(':')
        
        try:
            # Try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            
            if result == 0:
                # Service is up, return current time
                return datetime.now().isoformat()
            else:
                # Service is down
                return None
                
        except Exception as e:
            # Log error but don't fail the build
            print(f"Warning: Could not check {resource}: {e}")
            return None

Testing Checks
--------------

Test your check functions:

.. code-block:: python

    # In your tests
    def test_git_check():
        # Create test repo
        test_repo = Path("test_repo")
        test_repo.mkdir()
        subprocess.run(["git", "init"], cwd=test_repo)
        
        # Test check function
        result1 = check_git_repo(f"git://{test_repo}#main")
        
        # Make a commit
        (test_repo / "file.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "test"], cwd=test_repo)
        
        # Check should return different value
        result2 = check_git_repo(f"git://{test_repo}#main")
        assert result1 != result2

Best Practices
--------------

1. **Make Checks Fast**: They run on every build
2. **Handle Failures**: Don't crash on network errors
3. **Return Stable Values**: Same state should return same value
4. **Use Appropriate Granularity**: Check what actually affects your build
5. **Document Check Behavior**: Explain what triggers rebuilds

.. code-block:: python

    @check("db://*")
    def check_database(resource):
        """Check database schema version
        
        Returns: Schema version number from migrations table
        Rebuilds when: Database schema is migrated
        """
        # Implementation...

Integration Example
-------------------

Complete example using checks with rules:

.. code-block:: python

    from pyprod import check, rule, task, build

    # Check functions
    @check("https://data.gov/api/dataset")
    def check_dataset(resource):
        response = requests.head(resource)
        return response.headers.get('Last-Modified')

    @check("git://./analysis#main")  
    def check_analysis_code(resource):
        result = subprocess.run(
            ["git", "rev-parse", "main"],
            cwd="./analysis",
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    # Rules using checks
    @rule("data/raw.csv", depends="https://data.gov/api/dataset")
    def download_data(target, source):
        response = requests.get(source)
        with open(target, 'wb') as f:
            f.write(response.content)

    @rule("data/processed.csv", depends=["data/raw.csv", "git://./analysis#main"])
    def process_data(target, raw_data, analysis_code):
        run("python", "analysis/process.py", raw_data, target)

    @rule("report.pdf", depends="data/processed.csv")
    def generate_report(target, data):
        run("python", "generate_report.py", data, target)

    # Task to build everything
    @task(default=True)
    def all():
        build("report.pdf")

Next Steps
----------

- See :doc:`dependencies` for complex dependency graphs
- Learn about :doc:`../user-guide/watch-mode` for automatic rebuilds
- Explore :doc:`../cookbook/cloud-resources` for more cloud examples