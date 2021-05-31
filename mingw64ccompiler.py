from distutils import cygwinccompiler, sysconfig, ccompiler
import platform
import subprocess
import os
import sys


__all__ = ['patch']


def get_msvcr():
    assert platform.python_compiler().startswith('MSC v.19')
    # return ['ucrt', 'vcruntime140']
    return []


def customize_compiler(compiler, optimize=True):
    if optimize:
        options = ['-DMS_WIN64', '-Ofast', '-DNDEBUG', '-mtune=native', '-fwrapv']
    else:
        options = ['-DMS_WIN64', '-Wall']

    compiler.compiler = ['gcc'] + options
    compiler.compiler_so = ['gcc', '-mdll'] + options
    compiler.compiler_cxx = ['g++'] + options


def patch():
    assert platform.system() == 'Windows'
    cygwinccompiler.get_msvcr = get_msvcr
    sysconfig.customize_compiler = customize_compiler
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


def is_in_venv():
    b = sys.prefix == sys.base_prefix
    assert b == (sys._home is None)
    return not b


def customizepy_get_path():
    import site

    if is_in_venv():
        return site.getsitepackages()[0] + os.sep + 'sitecustomize.py'
    else:
        assert site.ENABLE_USER_SITE == True
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


def install():
    if not is_in_venv():
        specs_install()
    customizepy_install()


def uninstall():
    if not is_in_venv():
        specs_uninstall()
    customizepy_uninstall()


def help_msg_print():
    print('A monkey patch for cygwinccompiler which enables you to use MinGW-w64.')


def main():
    verbs = {'install': install, 'uninstall': uninstall, 'check': check,
             '-h': help_msg_print, '--help': help_msg_print}

    if len(sys.argv) == 1:
        sys.argv += ['-h']
    elif len(sys.argv) > 2 or sys.argv[1] not in verbs:
        print('Invalid command.')

    verbs[sys.argv[1]]()


if __name__ == '__main__':
    main()
