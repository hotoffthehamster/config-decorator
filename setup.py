#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of project: https://github.com/hotoffthehamster/config-decorator
# Copyright © 2019 Landon Bouma. All rights reserved.
#
# This program is free software:  you can redistribute it and/or modify
# it  under  the  terms  of  the  GNU Affero General Public License  as
# published by the  Free Software Foundation, either  version 3  of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY;  without even the implied warranty of
# MERCHANTABILITY or  FITNESS FOR A PARTICULAR PURPOSE.  See  the
# GNU   Affero   General   Public   License   for   more  details.
#
# If you lost the GNU Affero General Public License that ships with
# this code (the 'LICENSE' file), see <http://www.gnu.org/licenses/>.

"""
Packaging instruction for setup tools.

Refs:

  https://setuptools.readthedocs.io/

  https://packaging.python.org/en/latest/distributing.html

  https://github.com/pypa/sampleproject
"""

from setuptools import find_packages, setup

# *** Package requirements.

requirements = []

# *** Minimal setup() function -- Prefer using config where possible.

# (lb): All settings are in setup.cfg, except identifying packages.
# (We could find-packages from within setup.cfg, but it's convoluted.)

setup(
    install_requires=requirements,
    packages=find_packages(exclude=['tests*']),
    # Tell setuptools to determine the version
    # from the latest SCM (git) version tags.
    #
    # Without the following two lines, version would be, e.g.,
    #   $ python setup.py --version
    #   3.0.0a31
    # But with the next two lines, version reported as, e.g.,
    #   $ python setup.py --version
    #   3.0.0a32.dev3+g6f93d8c.d20190221
    # Or, if the latest commit is tagged, and your working directory
    # is clean, then the version reported (and, e.g., used on make-dist)
    # will be from the tag.
    # Ref:
    #   https://github.com/pypa/setuptools_scm
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
)

