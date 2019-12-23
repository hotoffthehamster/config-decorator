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

requirements = [
    # "Very simple Python library for color and formatting in terminal."
    # Forked (for italic "support") to:
    #  https://github.com/hotoffthehamster/ansi-escape-room
    # Forked from:
    #  https://gitlab.com/dslackw/colored
    # See wrapper file:
    #  nark/helpers/emphasis.py
    'ansi-escape-room',
    # Platform-specific directory magic.
    #  https://github.com/ActiveState/appdirs
    'appdirs',
    # Better INI/conf parser (preserves order, comments) than ConfigParser.
    #  https://github.com/DiffSK/configobj
    #  https://configobj.readthedocs.io/en/latest/
    'configobj >= 5.0.6',
    # https://github.com/scrapinghub/dateparser
    'dateparser',
    # Py2/3 support shim. (Higher-level than `six`.)
    #  https://pypi.org/project/future/
    #  https://python-future.org/
    'future',
    # Elapsed timedelta formatter, e.g., "1.25 days".
    'human-friendly_pedantic-timedelta >= 0.0.5',
    # https://github.com/collective/icalendar
    'icalendar',
    # https://bitbucket.org/micktwomey/pyiso8601
    'iso8601',
    # https://github.com/mnmelo/lazy_import
    'lazy_import',
    # Daylight saving time-aware timezone library.
    #  https://pythonhosted.org/pytz/
    'pytz',
    # For testing with dateparser,
    #   https://bitbucket.org/mrabarnett/mrab-regex
    #   https://pypi.org/project/regex/
    # FIXME/2019-02-19 18:13: Latest regex is broken.
    #   https://pypi.org/project/regex/2019.02.20/
    #   https://bitbucket.org/mrabarnett/mrab-regex/commits/
    #       5d8b8bb2b64b696cdbaa7bdc0dce4b462d311134#Lregex_3/regex.pyF400
    # Because of recent change to import line (was made self-referential):
    #      .tox/py37/lib/python3.7/site-packages/regex.py:400: in <module>
    #          import regex._regex_core as _regex_core
    #      E   ModuleNotFoundError: No module named 'regex._regex_core';
    #       'regex' is not a package
    'regex == 2019.02.18',
    # https://pythonhosted.org/six/
    'six',
    # https://www.sqlalchemy.org/
    # FIXME/2019-11-02: (lb): Migrate to SQLalchemy 1.3. Until then, stuck on 1.2.
    # 'sqlalchemy',
    'sqlalchemy >= 1.2.19, < 1.3',
    # Database gooser/versioner.
    #  https://pypi.org/project/sqlalchemy-migrate/
    #  https://sqlalchemy-migrate.readthedocs.io/en/latest/
    # 2019-02-21: (lb): Forked again! Package alt. that accepts static config.
    'sqlalchemy-migrate-dob >= 0.12.1',
    # https://github.com/regebro/tzlocal
    'tzlocal',
]

# *** Minimal setup() function -- Prefer using config where possible.

# (lb): All settings are in setup.cfg, except identifying packages.
# (We could find-packages from within setup.cfg, but it's convoluted.)

setup(
    install_requires=requirements,
    packages=find_packages(exclude=['tests*']),
    # Tell setuptools to determine the version
    # from the latest SCM (git) version tags.
    #
    # Without the following two lines, e.g.,
    #   $ python setup.py --version
    #   3.0.0a31
    # But with 'em, e.g.,
    #   $ python setup.py --version
    #   3.0.0a32.dev3+g6f93d8c.d20190221
    # Or, if the latest commit is tagged,
    # and your working directory is clean,
    # then the version reported (and, e.g.,
    # used on make-dist) will be from tag.
    # Ref:
    #   https://github.com/pypa/setuptools_scm
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
)

