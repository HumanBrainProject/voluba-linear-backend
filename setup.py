#!/usr/bin/env python3

import codecs
import os.path
import re
import sys

import setuptools


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Remember keep synchronized with the list of dependencies in tox.ini
tests_require = [
    "pytest",
]

needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner = ["pytest-runner"] if needs_pytest else []

setuptools.setup(
    name="voluba-linear-backend",
    version=find_version("linear_voluba", "__init__.py"),
    packages=["linear_voluba"],
    author="Yann Leprince",
    author_email="yann.leprince@cea.fr",
    install_requires=[
        "Flask ~= 1.0",
        "Flask-Cors",
        "flask-smorest ~= 0.18.3",
        "numpy",
    ],
    python_requires="~= 3.5",
    extras_require={
        "dev": tests_require + [
            "check-manifest",
            "flake8",
            "pep8-naming",
            "pre-commit",
            "pytest-cov",
            "readme_renderer",
            "tox",
        ],
        "tests": tests_require,
    },
    setup_requires=pytest_runner,
    tests_require=tests_require,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)
