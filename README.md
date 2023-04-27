# fASP
Efficient enumeration of fixed points in Boolean networks using answer set programming

# Install

You can install fASP with `pip` directly from the Package Index:

``` sh
$ python3 -m pip install fASP
```

You will also need the `clingo` ASP solver in your PATH.
Instructions are provided directly on the [Potassco pages](https://github.com/potassco/clingo/releases/).

# Run fASP from the command line

After installing `fASP` (and `clingo`), just run

```
$ fASP -h
usage: fASP [-h] [-v] [-m MAX] [-t TIME] [-e {conj,disj,source}] [infile]

Compute fixed points of complex Boolean networks. Copyright (C) 2023 Sylvain.Soliman@inria.fr and giang.trinh91@gmail.com GPLv3

positional arguments:
  infile                BoolNet (.bnet) file

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -m MAX, --max MAX     Maximum number of solutions (0 for all).
  -t TIME, --time TIME  Maximum number of seconds for search (0 for no-limit).
  -e {conj,disj,source}, --encoding {conj,disj,source}
                        ASP encoding to compute fixed points.
```
