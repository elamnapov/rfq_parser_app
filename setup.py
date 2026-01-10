"""
Setup script for RFQ Parser with C++ extension module

This setup.py builds the C++ extension using pybind11 and setuptools.
The C++ components provide high-performance validation and data structures
for RFQ processing in trading systems.
"""

import os
import sys
import subprocess
from pathlib import Path

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    """Extension that uses CMake to build"""

    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    """Custom build extension that runs CMake"""

    def build_extension(self, ext):
        if not isinstance(ext, CMakeExtension):
            super().build_extension(ext)
            return

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # Create build directory
        build_temp = Path(self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)

        # CMake configuration
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTS=OFF",  # Don't build tests when installing via pip
            "-DBUILD_PYTHON_MODULE=ON",
        ]

        # Build configuration
        build_args = ["--config", "Release"]

        # Platform-specific configuration
        if sys.platform.startswith("win"):
            # Windows: use Visual Studio generator
            cmake_args += [
                "-A", "x64" if sys.maxsize > 2**32 else "Win32",
            ]
            build_args += ["--", "/m"]
        else:
            # Unix: use Ninja or Make
            build_args += ["--", "-j4"]

        # Run CMake configure
        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args,
            cwd=build_temp
        )

        # Run CMake build
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args,
            cwd=build_temp
        )


# Read long description from README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

# Read version
version = "0.1.0"

setup(
    name="rfq-parser",
    version=version,
    author="Trading Desk Interview Candidate",
    description="RFQ Parser with LLM and C++ high-performance components",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rfq_parser",

    # Pure Python packages
    packages=find_packages(exclude=["tests", "tests.*", "cpp", "cpp.*"]),
    py_modules=["rfq_parser", "app"],

    # C++ extension module
    ext_modules=[CMakeExtension("rfq_cpp", sourcedir="cpp")],
    cmdclass={"build_ext": CMakeBuild},

    # Python version requirement
    python_requires=">=3.8",

    # Dependencies
    install_requires=[
        "streamlit>=1.28.0",
        "mistralai>=0.0.7",
        "python-dotenv>=1.0.0",
    ],

    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "mypy>=1.5.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },

    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: C++",
        "License :: OSI Approved :: MIT License",
    ],

    # Entry points
    entry_points={
        "console_scripts": [
            "rfq-parser=rfq_parser:main",
        ],
    },

    # Include package data
    include_package_data=True,
    zip_safe=False,
)
