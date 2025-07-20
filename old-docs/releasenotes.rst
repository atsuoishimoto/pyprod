Release Notes
================

0.10.0 (2025-4-29)
-----------------------------

- -w option

0.9.0 (2025-4-15)
-----------------------------

- Targets are execused simultaneously.

0.8.0 (2025-4-15)
-----------------------------

- Allow functions in the ``depends`` and ``uses``.


0.7.0 (2025-4-6)
-----------------------------

- Allow wildcard in the ``depends``.

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
