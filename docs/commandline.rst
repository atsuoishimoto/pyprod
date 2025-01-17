
.. _commandline:

Command line options
------------------------


usage: pyprod [-h] [-C DIRECTORY] [-f FILE] [-j JOB] [-r] [-v] [targets ...]

positional arguments:
  targets               Build targets. If no specific target is provided on the command line, the first target defined in the Prodfile is selected by default. Arguments containing ``=`` specifies the value of a :ref:`params <params>` (e.g., ``key=value``).

options:
  -h, --help            show this help message and exit
  -C, --directory DIRECTORY
                        Change to DIRECTORY before performing any operations
  -f, --file FILE       Use FILE as the Prodfile (default: 'PRODFILE.py')
  -j, --job JOB         Allow up to N jobs to run simultaneously (default: 1)
  -r, --rebuild         Rebuild all
  -v                    Increase verbosity level (default: 0)
