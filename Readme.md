# MinGW64 C Compiler

This is a monkey patch for cygwinccompiler which enables you to use MinGW-w64 as the compiler on Windows.

WARNING: Mixing CRT is dangerous. This is only for testing. Always prefer MSVC.

WARNING 2: This project is not widely tested. Use with caution.

## Usage

```bash
pip install git+https://github.com/imba-tjd/mingw64ccompiler
python -m mingw64ccompiler install_specs
python -m mingw64ccompiler install  # Works with venv
```

After this, the default compiler would be gcc, and it would link with ucrt.

Alternatively if you are confident with your compiler, in `setup.py`:

```py
__import__('mingw64ccompiler').patch()
```

For details, see [`mingw64ccompiler.py`](./mingw64ccompiler.py).

## Limitation

* I have never used Anaconda and know nothing about it
* Normal modules and Python are compiled and linked with `vcruntime140.dll`, but MinGW-w64 doesn't include it. Adding `-L sys.base_prefix` could work, and that directory is actually added in venv. I don't know waht to choose
* I can't find a way to run `cythonize` without `install`
* I don't know why but this works with `$env:SETUPTOOLS_USE_DISTUTILS="local"`
* `unknown conversion type character 'z' in format`
* Current API is inconvenient to disable optimize

## Reference

* https://stackoverflow.com/questions/57528555/how-do-i-build-against-the-ucrt-with-mingw-w64
* https://github.com/cython/cython/wiki/CythonExtensionsOnWindows#less-useful-information
* https://bugs.python.org/issue25251
