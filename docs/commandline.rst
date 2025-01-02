
.. _commandline:

Command line options
------------------------


usage: pyprod [-h] [-f FILE] [-j JOB] [-v] [-C DIRECTORY] [targets ...]

positional arguments:
  targets               Build targets. If no specific target is provided on the command line, the first target defined in the Prodfile is selected by default. Arguments containing ``=`` specifies the value of a :ref:`params <params>` (e.g., ``key=value``).

options:
  -f, --file FILE       Use FILE as the Prodfile (default: 'PRODFILE.py').
  -j, --job JOB         Allow up to N jobs to run simultaneously (default: 1).
  -C, --directory DIRECTORY
                        Change to DIRECTORY before performing any operations.
  -v                    Increase verbosity level (default: 0). Use multiple -v options to increase verbosity, up to a maximum of 3.


