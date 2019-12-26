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


# ***

class TestConfigDecoratorEmpty:
    # 2019-12-23: (lb): First test. 20% coverage.
    def test_empty_config(self):
        @section(None)
        class RootSection(object):
            pass

        rootcfg = RootSection
        assert isinstance(rootcfg, ConfigDecorator)
        assert isinstance(rootcfg._innerobj, object)


# ***

class TestConfigDecoratorNamed:
    # 2019-12-23: (lb): Second test. 21% coverage.
    def test_named_config(self):
        @section('foo', parent=None)
        class RootSection(object):
            pass

        rootcfg = RootSection
        assert isinstance(rootcfg, ConfigDecorator)
        assert isinstance(rootcfg._innerobj, object)


# ***

class TestConfigDecoratorNested:
    # 2019-12-23: (lb): Second test. 22% coverage.

    def test_nested_config(self):
        @section(None)
        class RootSection(object):
            pass

        @RootSection.section('foo')
        class NestedConfig(object):
            pass



# ***

class TestConfigDecoratorOverlay:
    # 2019-12-23: (lb): Third test. 31% coverage.

    def test_section_overlay(self):
        @section(None)
        class RootSection(object):
            def inner_function(self):
                return 'bar'

        @RootSection.section(None)
        class RootSectionOverlay(object):
            def __init__(self):
                pass

            @property
            @RootSection.setting(
                "Generated value.",
                hidden=True,
            )
            def inner_function(self):
                return RootSection._innerobj.inner_function()


# ***

class TestConfigDecoratorSameSectionRef:
    def test_same_section_ref(self):
        @section(None)
        class RootSection(object):
            pass

        @RootSection.section('foo')
        class RootSectionFoo1(object):
            def __init__(self):
                pass

        @RootSection.section('foo')
        class RootSectionFoo2(object):
            def __init__(self):
                pass


# ***

class TestConfigDecoratorPassive:
    def test_root_section_passive(self):
        @section
        class RootSection(object):
            pass


# ***

class TestSectionSettingDocstringDoc:
    def test_section_setting_implied_doc(self):
        @section(None)
        class RootSection(object):
            pass

        @RootSection.section(None)
        class RootSectionReal(object):
            @property
            @RootSection.setting()
            def foo(self):
                '''The foo setting does bar.'''


# ***

def generate_config_root_unknown_type():
    @section(None)
    class RootSection(object):
        pass

    @RootSection.section(None)
    class RootSectionReal(object):
        @property
        @RootSection.setting('test')
        def foo(self):
            # Default return value type will not be recognized.
            return object()

    return RootSection


class TestSectionSettingDefaultUnknownType:
    def test_section_method(self):
        with pytest.raises(NotImplementedError):
            rootcfg = generate_config_root_unknown_type()


# ***

def generate_config_root_unknown_bool_string():
    @section(None)
    class RootSection(object):
        pass

    @RootSection.section(None)
    class RootSectionReal(object):
        @property
        @RootSection.setting(
            "Validate bool string test, fail.",
            value_type=bool,
        )
        def validate_bool_string_fail_test(self):
            return 'Tralse'

    return RootSection


class TestSectionSettingDefaultUnknownBoolDefault:
    def test_section_method(self):
        rootcfg = generate_config_root_unknown_bool_string()
        with pytest.raises(ValueError):
            items = rootcfg.items()


# ***

def generate_config_root_fails_validation():
    def fail_validation(value):
        return False

    @section(None)
    class RootSection(object):
        pass

    @RootSection.section(None)
    class RootSectionReal(object):
        @property
        @RootSection.setting(
            "Validate fails test.",
            validate=fail_validation,
        )
        def validate_bool_string_fail_test(self):
            return None

    return RootSection


class TestSectionSettingValidationFail:
    def test_section_method_attribute(self):
        rootcfg = generate_config_root_fails_validation()
        with pytest.raises(ValueError):
            rootcfg.asobj.validate_bool_string_fail_test.value = 123

    def test_section_method_subscript(self):
        rootcfg = generate_config_root_fails_validation()
        with pytest.raises(ValueError):
            rootcfg['validate_bool_string_fail_test'] = 123

