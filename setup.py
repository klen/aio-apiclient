"""Setup the package."""


# Parse requirements
# ------------------
import pkg_resources
import pathlib


def parse_requirements(path: str) -> 'list[str]':
    with pathlib.Path(path).open() as requirements:
        return [str(req) for req in pkg_resources.parse_requirements(requirements)]


# Setup package
# -------------

from setuptools import setup


setup(
    extras_require={
        'tests': parse_requirements('requirements/requirements-tests.txt'),
        'httpx': ['httpx >= 0.20.0'],
        'aiohttp': ['aiohttp'],
    }
)

# pylama:ignore=E402,D
