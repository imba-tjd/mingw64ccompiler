import platform
import subprocess
import os
import sys
from setuptools._distutils import cygwinccompiler, ccompiler
from setuptools._distutils.cygwinccompiler import Mingw32CCompiler
import _distutils_hack


class Mingw64CCompiler(Mingw32CCompiler):
    compiler_type = 'mingw64'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        options = []
        if '32bit' in platform.architecture():
            options.append('-m32')
        if os.getenv('MINGW64CCOMPILER_DEBUG') or sys.flags.debug:
            options += ['-g', '-Wall']
        else:
            options += ['-O3', '-DNDEBUG', '-mtune=native', '-fwrapv']
        options_str = ' '.join(options)

        linker_so_options_str = '-shared'
        if not os.getenv('MINGW64CCOMPILER_DEBUG') and not sys.flags.debug:
            linker_so_options_str += ' -Wl,--as-needed'
        if '32bit' in platform.architecture():
            linker_so_options_str += ' -m32'

        self.set_executables(
            compiler=f'{self.cc} {options_str}',
            compiler_so=f'{self.cc} -shared {options_str}',
            compiler_cxx=f'{self.cxx} {options_str}',
            linker_exe=self.cc,
            linker_so=f'{self.linker_dll} {linker_so_options_str}',
        )


def suppress_warning(func):
    import warnings
    from functools import wraps

    @wraps(func)
    def f():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            func()
    return f


def patch():
    assert platform.system() == 'Windows'
    ccompiler.get_default_compiler = lambda _: 'mingw64'
    ccompiler.compiler_class['mingw64'] = ('cygwinccompiler', 'Mingw64CCompiler',
                                           'Mingw64 port of GNU C Compiler for Win32')
    cygwinccompiler.Mingw64CCompiler = Mingw64CCompiler
    sys.modules['distutils.cygwinccompiler'] = cygwinccompiler
    _distutils_hack.clear_distutils = suppress_warning(_distutils_hack.clear_distutils)


# MinGW ucrt spec patch

def _get_default_mingw_gcc():
    if platform.system() == 'Linux':
        return 'x86_64-w64-mingw32-gcc'
    else:
        return 'gcc'


def specs_get_content(modify=False, cc=_get_default_mingw_gcc()):
    content = subprocess.run([cc, '-dumpspecs'], capture_output=True, check=True, text=True).stdout
    if modify:
        content = content.replace('-lmsvcrt', '-lucrt') \
            .replace('*cpp:\n', '*cpp:\n-D_UCRT ') \
            .replace('*cc1plus:\n', '*cc1plus:\n-D_UCRT ')
    return content


def specs_get_path(cc=_get_default_mingw_gcc()):
    return subprocess.run([cc, '-print-libgcc-file-name'], capture_output=True, check=True, text=True).stdout[:-len('libgcc.a\n')] + 'specs'


def specs_install():
    with open(specs_get_path(), 'x', encoding='u8') as f:
        f.write(specs_get_content(True))


def specs_uninstall():
    os.remove(specs_get_path())


# Customizepy patch (do the monkey patch before any code run)

def is_in_venv():
    b = sys.prefix == sys.base_prefix  # equal when not in venv
    assert b == (sys._home is None)  # _home is None when not in venv
    return not b


def customizepy_get_path():
    import site

    if is_in_venv():
        return site.getsitepackages()[0] + os.sep + 'sitecustomize.py'

    assert site.ENABLE_USER_SITE
    os.makedirs(site.getusersitepackages(), exist_ok=True)
    return site.getusersitepackages() + os.sep + 'usercustomize.py'


def customizepy_install():
    content = '__import__("mingw64ccompiler").patch()' + '\n'
    cuspy_path = customizepy_get_path()

    with open(cuspy_path, 'x', encoding='u8') as f:
        f.write(content)


def customizepy_uninstall():
    cuspy_path = customizepy_get_path()
    with open(cuspy_path, encoding='u8') as f:
        content = f.read()
    if 'mingw64ccompiler' not in content:
        raise IOError(-1, 'mingw64ccompiler is not installed into customizepy.', cuspy_path)
    elif len(content) > len('__import__("mingw64ccompiler").patch()') + 5:
        raise IOError(-1, 'Additional content is in customizepy, abort.', cuspy_path)
    os.remove(cuspy_path)


# CLI

def check(cc='gcc'):
    gccv = subprocess.run([cc, '-v'], capture_output=True, check=True, text=True).stderr
    if 'Reading specs' in gccv:
        with open(specs_get_path(), encoding='u8') as f:
            spec_content = f.read()
    else:
        spec_content = specs_get_content(False)
    if 'lucrt' in spec_content:
        print('ucrt is linked with.')
    if 'lmsvcrt' in spec_content:
        print('Caution: msvcrt is linked with.')

    # won't fix: in venv but enable usersite
    cuspy_path = customizepy_get_path()
    if os.path.isfile(cuspy_path):
        with open(cuspy_path, encoding='u8') as f:
            cuspy_content = f.read()
        if 'mingw64ccompiler' in cuspy_content:
            print("mingw64ccompiler is installed into customizepy.")
            return
    print('mingw64ccompiler is not installed into customizepy.')


def help_msg_print():
    print('A monkey patch for cygwinccompiler which enables you to use MinGW-w64.')
    print('Valid commands:', list(verbs))


verbs = {'install': customizepy_install, 'uninstall': customizepy_uninstall,
         'install_specs': specs_install, 'uninstall_specs': specs_uninstall,
         'check': check, '-h': help_msg_print, '--help': help_msg_print}


def _main():
    if len(sys.argv) == 1:
        sys.argv += ['-h']
    elif len(sys.argv) > 2 or sys.argv[1] not in verbs:
        print('Invalid command.')

    verbs[sys.argv[1]]()


if __name__ == '__main__':
    _main()
