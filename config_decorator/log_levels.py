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

from __future__ import absolute_import, unicode_literals

import logging
import sys

from gettext import gettext as _

__all__ = (
    'must_verify_log_level',
    # Private:
    #  'LOG_LEVELS',
)


this = sys.modules[__name__]


# ***
# *** Config function: log level helpers.
# ***

this.LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


# MEH/2019-01-17: Deal with this when refactoring config:
#   If cli_log_level is wrong, app just logs a warning.
#   But for some reason, here, if sql_log_level is wrong,
#   app dies. Should probably just warning instead and
#   get on with life... print colorful stderr message,
#   but live.
#     See also: nark/nark/control.py and nark/nark/helpers/logging.py
#     have log_level functions, should probably consolidate this!
def must_verify_log_level(log_level_name):
    try:
        log_level = this.LOG_LEVELS[log_level_name.lower()]
    except KeyError:
        msg = _(
            "Unrecognized log level value in config: “{}”. Try one of: {}."
        ).format(log_level_name, ', '.join(this.LOG_LEVELS))
        raise SyntaxError(msg)
    return log_level


def get_log_level_safe(log_level_name):
    must_verify_log_level(log_level_name)
    # FIXME/EXPLAIN/2019-01-17: What only do this for nark,
    #   and not also for cli_log_level ?
    #   TEST: Per comment, test ``dob complete`` and see if dob logs
    #     anything (and if so, apply this logic to cli_log_level).

    # (lb): A wee bit of a hack! Don't log during the dob-complete
    #   command, lest yuck!
    if (len(sys.argv) == 2) and (sys.argv[1] == 'complete'):
        # Disable for dob-complete.
        return logging.CRITICAL + 1
    return log_level_name

