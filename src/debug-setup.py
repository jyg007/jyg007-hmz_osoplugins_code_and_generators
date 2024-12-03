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

from setuptools import find_packages, setup


def default_configure() -> dict[str, typing.Any]:
    """
    Offline Signing Orchestrator default compilation/installation configuration
    """

    return dict(
        packages=find_packages(include=["oso_harmonize_plugins"]),
        test_suite="pytest",
    )


setup(
    name="oso-harmonize-plugins",
    **default_configure(),
)
