from distutils import cygwinccompiler, sysconfig, ccompiler
# from setuptools._distutils import cygwinccompiler, sysconfig, ccompiler
import platform
import subprocess
import os
import sys


# ccompiler monkey patch

def get_msvcr():
    assert platform.python_compiler().startswith('MSC v.19')
    # return ['ucrt', 'vcruntime140']
    return []


def customize_compiler(compiler):
    '''Was called in build_ext.py. Original function doesn't do anything on Win.'''
    options = []
    if '64bit' in platform.architecture():
        options.append('-DMS_WIN64')
    else:
        options.append('-m32')
    if not os.getenv('MINGW64CCOMPILER_DEBUG'):
        options += ['-Ofast', '-DNDEBUG', '-mtune=native', '-fwrapv']
    else:
        options += ['-Wall']

    compiler.compiler = [compiler.compiler[0]] + options  # Original: ['gcc', '-O', '-Wall']
    compiler.compiler_so = [compiler.compiler_so[0], '-shared'] + options  # Original: ['gcc', '-mdll', '-O', '-Wall']
    compiler.compiler_cxx = [compiler.compiler_cxx[0]] + options
    compiler.linker_so.append('-Wl,--as-needed')
    if '32bit' in platform.architecture():
        compiler.linker_so.append('-m32')


# MinGW ucrt spec patch

def patch():
    assert platform.system() == 'Windows'
    cygwinccompiler.get_msvcr = get_msvcr
    sysconfig.customize_compiler = customize_compiler  # Note it's distutils' module rather than sysconfig library
    ccompiler.get_default_compiler = lambda _: 'mingw32'


def specs_get_content(modify=True):
    content = subprocess.run(['gcc', '-dumpspecs'], capture_output=True, check=True, text=True).stdout
    if modify:
        content = content.replace('-lmsvcrt', '-lucrt') \
            .replace('*cpp:\n', '*cpp:\n-D_UCRT ') \
            .replace('*cc1plus:\n', '*cc1plus:\n-D_UCRT ')
    return content


def specs_get_path():
    return subprocess.run(['gcc', '-print-libgcc-file-name'], capture_output=True, check=True, text=True).stdout[:-len('libgcc.a\n')] + 'specs'


def specs_install():
    with open(specs_get_path(), 'x', encoding='u8') as f:
        f.write(specs_get_content())


def specs_uninstall():
    os.remove(specs_get_path())


# Customizepy patch. (do the monkey patch before any code run)

def is_in_venv():
    b = sys.prefix == sys.base_prefix  # equal when not in venv
    assert b == (sys._home is None)  # _home is None when not in venv
    return not b


def customizepy_get_path():
    import site

    if is_in_venv():
        return site.getsitepackages()[0] + os.sep + 'sitecustomize.py'
    else:
        assert site.ENABLE_USER_SITE
        return site.getusersitepackages() + os.sep + 'usercustomize.py'


def customizepy_install():
    content = f'__import__("mingw64ccompiler").patch()' + '\n'
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

def check():
    gccv = subprocess.run(['gcc', '-v'], capture_output=True, check=True, text=True).stderr
    if 'Reading specs' in gccv:
        with open(specs_get_path(), encoding='u8') as f:
            spec_content = f.read()
    else:
        spec_content = specs_get_content(False)
    if 'lucrt' in spec_content:
        print('ucrt is linked with.')
    if 'lmsvcrt' in spec_content:
        print('Caution: msvcrt is linked with.')

    cuspy_path = customizepy_get_path()
    if os.path.exists(cuspy_path):
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
