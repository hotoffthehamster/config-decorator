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
"""Defines a class that maps subscription to attribute lookup.
"""

from __future__ import absolute_import, unicode_literals

__all__ = (
    'Subscriptable',
)


class Subscriptable(object):
    """A base class that maps ``object['key']`` to either ``object.key.value`` or ``object.key``.

    .. automethod:: __getitem__
    """

    def __init__(self):
        super(Subscriptable, self).__init__()
        pass

    def __getitem__(self, name):
        """Makes an otherwise non-subscriptable object subscriptable.

           I.e., calling ``obj['key']`` maps to ``obj.key``.

           Or, put another way, the user can access data at *obj['key']* as well as *obj.key*.

        .. Note::

            If the derived class has a ``value`` attribute, that attribute
            is returned instead.

            E.g., given a ``ConfigDecorator`` settings configuration,
            you can call either ``cfg['foo']['bar'].value`` or more
            simply ``cfg.foo.bar``.

        Args:
            name: Attribute name to lookup.
        """
        item = getattr(self, name)
        try:
            return item.value
        except AttributeError:
            return item

