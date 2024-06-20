# MinGW64 C Compiler

A monkey patch for cygwinccompiler which enables you to use MinGW-w64 as the default compiler on Windows.

If you want to try Cython but doesn't have MSVC installed, this is for you.

WARNING: This project is not widely tested and is only for hobby.

## Usage

```bash
pip install git+https://github.com/imba-tjd/mingw64ccompiler
python -m mingw64ccompiler install_specs  # ① Run once
python -m mingw64ccompiler install        # ② Run in every venv
```

Then `python setup.py build_ext -i`, `cythonize -i`, `mypyc`, `pip wheel .`, `pip install --no-build-isolation` will use gcc as the default compiler, and it would link with ucrt.

To programmally patch, use `__import__('mingw64ccompiler').patch()`. This doesn't require you to use `install` command firstly, but `cythonize` and other CLI tools won't work.

To use `-Wall` rather than `-O3`, set `MINGW64CCOMPILER_DEBUG` environment variable.

## How it works

* ① Create a spec file in mingw installation dir to let gcc link with ucrt. This may not work. This is not required if your mingw is compiled with `--with-default-msvcrt=ucrt`.
* ② Use `sitecustomize.py` to overriede the return value of `get_default_compiler()` so that the default compiler is gcc.

## Limitation

* `unknown conversion type character 'z' in format` when using `from cpython cimport array`
* I have never used Anaconda and know nothing about it

## Known to fail

* psutil: https://github.com/giampaolo/psutil/issues/330
* lxml: Could not find function xmlCheckVersion in library libxml2. Is libxml2 installed?
* llvmlite: requires cmake
* numpy: mt19937.h:27:1: error: multiple storage classes in declaration specifiers
* scipy: BLAS & LAPACK libraries need to be installed
* pyodbc: it sets MSVC-specific args in setup.py
* pytorch extension: when *IS_WINDOWS*, all compiler related code is set to use MSVC

## Reference

* https://stackoverflow.com/questions/57528555/how-do-i-build-against-the-ucrt-with-mingw-w64
* https://github.com/cython/cython/wiki/CythonExtensionsOnWindows#less-useful-information
