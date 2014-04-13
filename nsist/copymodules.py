import os
import shutil
import sys
import zipfile, zipimport

PY2 = sys.version_info[0] == 2
running_python  = '.'.join(str(x) for x in sys.version_info[:2])

class ExtensionModuleMismatch(ImportError):
    pass

extensionmod_errmsg = """Found an extension module that will not be usable on %s:
%s
Put Windows packages in pynsist_pkgs/ to avoid this."""

def check_ext_mod(path, target_python):
    if path.endswith('.so'):
        raise ExtensionModuleMismatch(extensionmod_errmsg % ('Windows', path))
    elif path.endswith('.pyd') and not target_python.startswith(running_python):
        # TODO: From Python 3.2, extension modules can restrict themselves
        # to a stable ABI. Can we detect this?
        raise ExtensionModuleMismatch(extensionmod_errmsg % ('Python '+target_python, path))

def check_package_for_ext_mods(path, target_python):
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            check_ext_mod(os.path.join(path, dirpath, filename), target_python)

def copy_zipmodule(loader, modname, target):
    file = loader.get_filename(modname)
    prefix = loader.archive + '/' + loader.prefix
    assert file.startswith(prefix)
    path_in_zip = file[len(prefix):]
    zf = zipfile.ZipFile(loader.archive)
    if loader.is_package(modname):
        pkgdir, basename = path_in_zip.rsplit('/', 1)
        assert basename.startswith('__init__')
        pkgfiles = [f for f in zf.namelist() if f.startswith(pkgdir)]
        zf.extractall(target, pkgfiles)
    else:
        zf.extract(path_in_zip, target)

if not PY2:
    import importlib
    import importlib.abc
    import importlib.machinery

    class ModuleCopier:
        """Finds and copies importable Python modules and packages.

        This is the Python >3.3 version and uses the `importlib` package to
        locate modules.
        """
        def __init__(self, py_version, path=None):
            self.py_version = py_version
            self.path = path if (path is not None) else ([''] + sys.path)

        def copy(self, modname, target):
            """Copy the importable module 'modname' to the directory 'target'.

            modname should be a top-level import, i.e. without any dots.
            Packages are always copied whole.

            This can currently copy regular filesystem files and directories,
            and extract modules and packages from appropriately structured zip
            files.
            """
            loader = importlib.find_loader(modname, self.path)
            if loader is None:
                raise ImportError('Could not find %s' % modname)
            pkg = loader.is_package(modname)

            if isinstance(loader, importlib.machinery.ExtensionFileLoader):
                check_ext_mod(loader.path, self.py_version)
                shutil.copy2(loader.path, target)

            elif isinstance(loader, importlib.abc.FileLoader):
                file = loader.get_filename(modname)
                if pkg:
                    pkgdir, basename = os.path.split(file)
                    assert basename.startswith('__init__')
                    check_package_for_ext_mods(pkgdir, self.py_version)
                    dest = os.path.join(target, modname)
                    shutil.copytree(pkgdir, dest,
                                    ignore=shutil.ignore_patterns('*.pyc'))
                else:
                    shutil.copy2(file, target)

            elif isinstance(loader, zipimport.zipimporter):
                copy_zipmodule(loader, modname, target)
else:
    import imp

    class ModuleCopier:
        """Finds and copies importable Python modules and packages.

        This is the Python 2.7 version and uses the `imp` package to locate
        modules.
        """
        def __init__(self, py_version, path=None):
            self.py_version = py_version
            self.path = path if (path is not None) else ([''] + sys.path)
            self.zip_paths = [p for p in self.path if zipfile.is_zipfile(p)]

        def copy(self, modname, target):
            """Copy the importable module 'modname' to the directory 'target'.

            modname should be a top-level import, i.e. without any dots.
            Packages are always copied whole.

            This can currently copy regular filesystem files and directories,
            and extract modules and packages from appropriately structured zip
            files.
            """
            info = imp.find_module(modname, self.path)
            path = info[1]
            modtype = info[2][2]

            if modtype == imp.C_EXTENSION:
                check_ext_mod(path, self.py_version)

            if modtype in (imp.PY_SOURCE, imp.C_EXTENSION):
                shutil.copy2(path, target)

            elif modtype == imp.PKG_DIRECTORY:
                check_package_for_ext_mods(path, self.py_version)
                dest = os.path.join(target, modname)
                shutil.copytree(path, dest,
                                ignore=shutil.ignore_patterns('*.pyc'))
            else:
                # Search all ZIP files in self.path for the module name
                # NOTE: `imp.find_module(...)` will *not* find modules in ZIP
                #       files, so we have to check each file for ourselves
                for zpath in self.zip_path:
                    loader = zipimport.zipimporter(zpath)
                    if loader.find_module(modname) is None:
                        continue
                    copy_zipmodule(loader, modname, target)


def copy_modules(modnames, target, py_version, path=None):
    """Copy the specified importable modules to the target directory.
    
    By default, it finds modules in sys.path - this can be overridden by passing
    the path parameter.
    """
    mc = ModuleCopier(py_version, path)
    files_in_target_noext = [os.path.splitext(f)[0] for f in os.listdir(target)]
    
    for modname in modnames:
        if modname in files_in_target_noext:
            # Already there, no need to copy it.
            continue
        mc.copy(modname, target)
    
    if not modnames:
        # NSIS abhors an empty folder, so give it a file to find.
        with open(os.path.join(target, 'placeholder'), 'w') as f:
            f.write('This file only exists so NSIS finds something in this directory.')