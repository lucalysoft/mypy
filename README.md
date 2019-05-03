mypyc: Mypy to Python C Extension Compiler
==========================================

*Mypyc is (mostly) not yet useful for general Python development.*

Mypyc is a compiler that compiles mypy-annotated, statically typed
Python modules into Python C extensions. Currently our primary focus
is on making mypy faster through compilation---the default mypy wheels
are compiled with mypyc.

Mypyc compiles what is essentially a Python language variant using "strict"
semantics. This means (among some other things):

 * Most type annotations are enforced at runtime (raising ``TypeError`` on mismatch)

 * Classes are compiled into extension classes without ``__dict__``
   (much, but not quite, like if they used ``__slots__``)

 * Monkey patching doesn't work

 * Instance attributes won't fall back to class attributes if undefined

 * Metaclasses not supported

 * Also there are still a bunch of bad bugs and unsupported features :)


macOS Requirements
------------------

* macOS Sierra or later

* Xcode command line tools

* Python 3.6 (64-bit) from python.org (other versions likely *won't*
  work right now)

Linux Requirements
------------------

* A recent enough C/C++ build environment

* Python 3.5+ (64-bit)

Windows Requirements
--------------------

* Windows has been tested with Windows 10 and MSVC 2017.

* Python 3.5+ (64-bit)

Quick Start for Contributors
----------------------------

First clone the mypyc git repository *and git submodules*:

    $ git clone --recurse-submodules https://github.com/mypyc/mypyc.git
    $ cd mypyc

Optionally create a virtualenv (recommended):

    $ virtualenv -p python3 <directory>
    $ source <directory>/bin/activate

Then install the dependencies:

    $ python3 -m pip install -r mypyc/external/mypy/test-requirements.txt

Now you can run the tests:

    $ pytest mypyc

Look at the [issue tracker](https://github.com/mypyc/mypyc/issues)
for things to work on. Please express your interest in working on an
issue by adding a comment before doing any significant work, since
development is currently very active and there is real risk of duplicate
work.

Documentation
-------------

We have some [developer documentation](doc/dev-intro.md).

Development Status and Roadmap
------------------------------

These are the current planned major milestones:

1. [DONE] Support a smallish but useful Python subset. Focus on compiling
   single modules, while the rest of the program is interpreted and does not
   need to be type checked.

2. [DONE] Support compiling multiple modules as a single compilation unit (or
   dynamic linking of compiled modules).  Without this inter-module
   calls will use slower Python-level objects, wrapper functions and
   Python namespaces.

3. [DONE] Mypyc can compile mypy.

4. [DONE] Optimize some important performance bottlenecks.

5. [PARTIALLY DONE] Generate useful errors for code that uses unsupported Python
   features instead of crashing or generating bad code.

6. [DONE] Release a version of mypy that includes a compiled mypy.

7a. More feature/compatability work. (100% compatability is distinctly
    an anti-goal, but more than we have now is a good idea.)

7b. Support compiling Black, which is a prominent tool that could benefit
    and has maintainer buy-in.
    (Let us know if you maintain a another Python tool or library and are
     interested in working with us on this!)

7c. More optimization! Code size reductions in particular are likely to
    be valuable and will speed up mypyc compilation.

8.  We'll see! Adventure is out there!

Future
------

We have some ideas for
[future improvements and optimizations](doc/future.md).
