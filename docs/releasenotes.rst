Release Notes
================

0.6.0 (2025-4-6)
-----------------------------

- Ignore None or falsy values in the ``depends`` and ``uses`` in the rule.

0.5.0 (2025-2-12)
-----------------------------

- Added ``default`` to the ``@task``.
- Removed ``depends`` from thr ``@task``.
- Added --use-git commandline option.

0.4.0 (2025-1-17)
-------------------------
- Swapped the behavior of quote() and squote() to make their naming more intuitive.
- Add @task decorator.
- Change the parameter name target to targets.
- Added --rebuild option.

0.3.0 (2025-01-03)
------------------
- Arguments for build and check function are converted to string.
- Add built-in functions.
- Validate rule dependencies.
