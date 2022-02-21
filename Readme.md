# MinGW64 C Compiler

A monkey patch for cygwinccompiler which enables you to use MinGW-w64 as the compiler on Windows.

WARNING: This project is not widely tested and is only for hobby. Always prefer MSVC.

## Usage

```bash
pip install git+https://github.com/imba-tjd/mingw64ccompiler
python -m mingw64ccompiler install_specs  # Run once
python -m mingw64ccompiler install        # Works with venv
```

Then `python setup.py build_ext -i`, `cythonize -i`, `mypyc`, `pip wheel .` will use gcc as the default compiler, and it would link with ucrt.

To programmally patch, use `__import__('mingw64ccompiler').patch()`. This doesn't require you to use `install` command firstly, but `cythonize` and other CLI tools won't work.

To use `-Wall` rather than `-Ofast`, set `MINGW64CCOMPILER_DEBUG` environment variable.

## Limitation

* `unknown conversion type character 'z' in format` when using `from cpython cimport array`
* I have never used Anaconda and know nothing about it

## Known to fail

* psutil: https://github.com/giampaolo/psutil/issues/330
* lxml: Could not find function xmlCheckVersion in library libxml2. Is libxml2 installed?
* llvmlite: requires cmake
* numpy: still says VC++14 is required. Besides it may need openblas
* scipy: BLAS & LAPACK libraries need to be installed

## Reference

* https://stackoverflow.com/questions/57528555/how-do-i-build-against-the-ucrt-with-mingw-w64
* https://github.com/cython/cython/wiki/CythonExtensionsOnWindows#less-useful-information
