#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import typing

from Cython.Build import build_ext, cythonize
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py


class NullBuildPy(build_py):
    """
    Skip building python files, such that a pure python project can masqarade
    as a pure Cython project.
    """

    def run(self) -> None:
        return


def default_configure() -> dict[str, typing.Any]:
    """
    Offline Signing Orchestrator default compilation/installation configuration
    """
    return dict(
        packages=find_packages(include=["oso_harmonize_plugins"]),
        cmdclass={
            "build_py": NullBuildPy,
            "build_ext": build_ext,
        },
        test_suite="pytest",
    )


setup(
    name="oso-harmonize-plugins",
    ext_modules=cythonize(["oso_harmonize_plugins/**/*.py"]),
    **default_configure(),
)

