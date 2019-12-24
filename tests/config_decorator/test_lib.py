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

import pytest

from config_decorator import section


class TestConfigDecorator:
    @pytest.mark.parametrize('storetype', ['sqlalchemy'])
#    def test_get_store_valid(self, controller, storetype):
    def test_get_store_valid(self, storetype):
        """Make sure we recieve a valid ``store`` instance."""
        return
        # [TODO]
        # Once we got backend registration up and running this should be
        # improved to check actual store type for that backend.
        controller.config['db.store'] = storetype
        assert isinstance(controller._get_store(), BaseStore)

