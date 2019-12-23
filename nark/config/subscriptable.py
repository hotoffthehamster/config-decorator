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

__all__ = (
    'Subscriptable',
)


class Subscriptable(object):
    """"""

    def __init__(self):
        super(Subscriptable, self).__init__()
        pass

    def __getitem__(self, name):
        """Makes object[subscripting] to same-named object.attribute.
           E.g., user can access data at `obj['key']` as well as `obj.key`.
        """
        item = getattr(self, name)
        try:
            return item.value
        except AttributeError:
            return item

