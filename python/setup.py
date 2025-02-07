from setuptools import setup
from setuptools.command.build_ext import build_ext
from distutils.core import Extension, Command
from distutils.command.build import build
from distutils.command.config import config
from distutils.msvccompiler import MSVCCompiler
import sysconfig
import string
import sys

mkobjs = ["column", "custom", "derived", "fileio", "field",
          "format", "handler", "persist", "remap", "std",
          "store", "string", "table", "univ", "view", "viewx"]


class build_mk(build):
    def initialize_options(self):
        # build in builds directory by default, unless specified otherwise
        build.initialize_options(self)
        self.build_base = "../builds"


class build_mkext(build_ext):
    def finalize_options(self):
        self.run_command("config")

        # force use of C++ compiler (helps on some platforms)
        import os

        cc = os.environ.get("CXX", sysconfig.get_config_var("CXX"))
        if cc:
            os.environ["CC"] = cc

        build_ext.finalize_options(self)

    def build_extension(self, ext):
        # work around linker problem with MacPython 2.3
        if sys.platform == "darwin":
            try:
                self.compiler.linker_so.remove("-Wl,-x")
            except:
                pass
        # work around linker problem with Linux, Python 2.2 and earlier:
        # despite setting $CC above, still uses Python compiler
        if sys.platform == "linux2":
            try:
                ext.libraries.append("stdc++")
            except:
                pass
        if ext.name == "Mk4py":
            if isinstance(self.compiler, MSVCCompiler):
                suffix = ".obj"
                if self.debug:
                    prefix = "../builds/msvc60/mklib/Debug/"
                else:
                    prefix = "../builds/msvc60/mklib/Release/"
            else:
                suffix = ".o"
                prefix = "../builds/"
            for i in range(len(ext.extra_objects)):
                nm = ext.extra_objects[i]
                if nm in mkobjs:
                    if "." in nm:
                        nm = nm + suffix
                    nm = prefix + nm
                    ext.extra_objects[i] = nm
        build_ext.build_extension(self, ext)


class test_regrtest(Command):
    # Original version of this class posted
    # by Berthold Hoellmann to distutils-sig@python.org
    description = "test the distribution prior to install"

    user_options = [
        ("build-base=", "b",
         "base build directory (default: 'build.build-base')"),
        ("build-purelib=", None,
         "build directory for platform-neutral distributions"),
        ("build-platlib=", None,
         "build directory for platform-specific distributions"),
        ("build-lib=", None,
         "build directory for all distribution (defaults to either " +
         "build-purelib or build-platlib"),
        ("test-dir=", None,
         "directory that contains the test definitions"),
        ("test-options=", None,
         "command-line options to pass to test.regrtest")
        ]

    def initialize_options(self):
        self.build_base = None
        # these are decided only after 'build_base' has its final value
        # (unless overridden by the user or client)
        self.build_purelib = None
        self.build_platlib = None
        self.test_dir = "test"
        self.test_options = None

    def finalize_options(self):
        build = self.distribution.get_command_obj("build")
        build_options = ("build_base", "build_purelib", "build_platlib")
        for option in build_options:
            val = getattr(self, option)
            if val:
                setattr(build, option, getattr(self, option))
        build.ensure_finalized()
        for option in build_options:
            setattr(self, option, getattr(build, option))

    def run(self):

        # Invoke the 'build' command to "build" pure Python modules
        # (ie. copy 'em into the build tree)
        self.run_command("build")

        # remember old sys.path to restore it afterwards
        old_path = sys.path[:]

        # extend sys.path
        sys.path.insert(0, self.build_purelib)
        sys.path.insert(0, self.build_platlib)
        sys.path.insert(0, self.test_dir)

        # Use test.regrtest, unlike the original version of this class
        #import test.regrtest

        # jcw 2004-04-26 - why do I need to add these here to find the tests?
        #import leaktest - not very portable
        #import test_inttypes
        #import test_stringtype
        #import test_hash - doesn't work
        # jcw end

        test.regrtest.STDTESTS = []
        test.regrtest.NOTTESTS = []

        if self.test_options:
            sys.argv[1:] = string.split(self.test_options, " ")
        else:
            del sys.argv[1:]

        # remove stale modules
        del sys.modules["metakit"]
        try:
            del sys.modules["Mk4py"]
        except:
            pass

        self.announce("running tests")
        test.regrtest.main(testdir=self.test_dir)

        # restore sys.path
        sys.path = old_path[:]


#try:
#    import metakit
#except:
#    metakit = sys.modules['metakit']

setup(
    cmdclass={"build": build_mk, "build_ext": build_mkext, "test": test_regrtest,},
    ext_modules=[
        Extension(
            "Mk4py",
            sources=["PyProperty.cpp", "PyRowRef.cpp", "PyStorage.cpp", "PyView.cpp", "scxx/PWOImp.cpp",] + [("../src/" + n + ".cpp") for n in mkobjs],
            include_dirs=["scxx", "../include", "./py3c/include"],
            #extra_objects=mkobjs,
            extra_compile_args=["-std=gnu++2a", "-g", "-ggdb", "-O0", "-fcf-protection=full"],
        )
    ],
)

## Local Variables:
## compile-command: "python setup.py build -b ../builds"
## End:
