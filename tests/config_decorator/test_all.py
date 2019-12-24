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

import factory
import fauxfactory
import pytest

from config_decorator import section
from config_decorator.config_decorator import ConfigDecorator
from config_decorator.subscriptable import Subscriptable


def generate_config_root():

    @section(None)
    class ConfigRoot(object):
        def inner_function(self):
            return 'foo'


    @ConfigRoot.section(None)
    class ConfigRootOverlay(Subscriptable):
        def __init__(self):
            pass

        # ***

        @property
        @ConfigRoot.setting(
            "Hidden test.",
            hidden=True,
        )
        def inner_function(self):
            return ConfigRoot._innerobj.inner_function()

        # ***

        @property
        @ConfigRoot.setting(
            "Choices test.",
            choices=['', 'one', 'two', 'three'],
        )
        def choices_test(self):
            return ''

        # ***

        @property
        @ConfigRoot.setting(
            "Different Name test.",
            name='real-option-name',
        )
        def real_option_name(self):
            return ''

        # ***

        def some_type_conversation(value):
            if isinstance(value, int):
                return value
            return int(value) + 100

        @property
        @ConfigRoot.setting(
            "Value Type test.",
            value_type=some_type_conversation,
        )
        def value_type_test(self):
            return '1'

        # ***

        @property
        @ConfigRoot.setting(
            "Allow None test.",
            value_type=bool,
            allow_none=True,
        )
        def allow_none_test(self):
            return None

        # ***

        @property
        @ConfigRoot.setting(
            "Ephemeral test.",
            ephemeral=True,
        )
        def ephemeral_test(self):
            return 'This will not be saved!'

        # ***

        def must_validate_foo(some_value):
            return some_value

        @property
        @ConfigRoot.setting(
            "Validate pass test.",
            validate=must_validate_foo,
        )
        def pass_validate_test(self):
            return 'This will not be saved!'

        # ***

        def fail_validate_foo(some_value):
            msg = 'Validation failed'
            raise SyntaxError(msg)

        @property
        @ConfigRoot.setting(
            "Validate fail test.",
            validate=fail_validate_foo,
        )
        def fail_validate_test(self):
            return 'This will not be saved!'


    @ConfigRoot.section('level1')
    class ConfigRootLevel1(Subscriptable):
        def __init__(self):
            pass

        @property
        @ConfigRoot.setting(
            "Test sub config setting, level1.foo",
        )
        def foo(self):
            return 'baz'


    @ConfigRootLevel1.section('level2')
    class ConfigRootLevel2(Subscriptable):
        def __init__(self):
            pass

        @property
        @ConfigRoot.setting(
            "Test sub sub config setting, level1.level2.bar",
        )
        def baz(self):
            return 'bat'

    return ConfigRoot


class TestConfigDecoratorAsDict:
    def test_something(self):
        rootcfg = generate_config_root()
        assert isinstance(rootcfg, ConfigDecorator)
        assert isinstance(rootcfg._innerobj, object)

        settings = rootcfg.as_dict()


class TestConfigDecoratorSetDefault:
    def test_something(self):
        rootcfg = generate_config_root()
        rootcfg.setdefault('totally-unknown-key', 123)
        rootcfg.setdefault('totally-unknown-key.subsection.too', False)
        rootcfg.setdefault('level1.foo', 'exercise different branch on known sub key')
        with pytest.raises(TypeError):
            rootcfg.setdefault('missing.value')

