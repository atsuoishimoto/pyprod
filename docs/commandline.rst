
.. _commandline:

Command line options
------------------------


usage: pyprod [-h] [-C DIRECTORY] [-f FILE] [-j JOB] [-r] [-g] [-w [WATCH ...]] [-v] [-V] [targets ...]


PyProd - More makable than make

positional arguments:
  targets               Build targets

options:
  -h, --help            show this help message and exit
  -C, --directory DIRECTORY
                        Change to DIRECTORY before performing any operations
  -f, --file FILE       Use FILE as the Prodfile (default: 'Prodfile.py')
  -j, --job JOB         Allow up to N jobs to run simultaneously (default: 1)
  -r, --rebuild         Rebuild all
  -g, --use-git         Get file timestamps from Git
                        directories to watch
  -v                    Increase verbosity level (default: 0)
  -V, --version         Show version
