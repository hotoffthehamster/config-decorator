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
from config_decorator.config_decorator import ConfigDecorator
from config_decorator.subscriptable import Subscriptable


class TestConfigDecoratorEmpty:
    # 2019-12-23: (lb): First test. 20% coverage.
    def test_empty_config(self):
        @section(None)
        class ConfigRoot(object):
            pass

        rootcfg = ConfigRoot
        assert isinstance(rootcfg, ConfigDecorator)
        assert isinstance(rootcfg._innerobj, object)


class TestConfigDecoratorNamed:
    # 2019-12-23: (lb): Second test. 21% coverage.
    def test_named_config(self):
        @section('foo', parent=None)
        class ConfigRoot(object):
            pass

        rootcfg = ConfigRoot
        assert isinstance(rootcfg, ConfigDecorator)
        assert isinstance(rootcfg._innerobj, object)


class TestConfigDecoratorNested:
    # 2019-12-23: (lb): Second test. 22% coverage.

    def test_nested_config(self):
        @section(None)
        class ConfigRoot(object):
            pass

        @ConfigRoot.section('foo')
        class NestedConfig(Subscriptable):
            pass



class TestConfigDecoratorOverlay:
    # 2019-12-23: (lb): Third test. 31% coverage.

    def test_section_overlay(self):
        @section(None)
        class ConfigRoot(object):
            def inner_function(self):
                return 'bar'

        @ConfigRoot.section(None)
        class ConfigRootOverlay(Subscriptable):
            def __init__(self):
                pass

            @property
            @ConfigRoot.setting(
                "Generated value.",
                hidden=True,
            )
            def inner_function(self):
                return ConfigRoot._innerobj.inner_function()


class TestConfigDecoratorSameSectionRef:
    def test_same_section_ref(self):
        @section(None)
        class ConfigRoot(object):
            pass

        @ConfigRoot.section('foo')
        class ConfigRootFoo1(Subscriptable):
            def __init__(self):
                pass

        @ConfigRoot.section('foo')
        class ConfigRootFoo2(Subscriptable):
            def __init__(self):
                pass


class TestConfigDecoratorPassive:
    def test_root_section_passive(self):
        @section
        class ConfigRoot(object):
            pass


class TestSectionSettingDocstringDoc:
    def test_section_setting_implied_doc(self):
        @section(None)
        class ConfigRoot(object):
            pass

        @ConfigRoot.section(None)
        class ConfigRootReal(object):
            @property
            @ConfigRoot.setting()
            def foo(self):
                '''The foo setting does bar.'''

