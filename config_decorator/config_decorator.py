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
'''Pythonic @decorator syntax for defining robust user config'''

from __future__ import absolute_import, unicode_literals

import inspect
from collections import OrderedDict
from functools import update_wrapper

from gettext import gettext as _

from .key_chained_val import KeyChainedValue
from .subscriptable import Subscriptable

__all__ = (
    'section',
    # PRIVATE:
    # 'ConfigDecorator',
)


class ConfigDecorator(Subscriptable):
    def __init__(self, cls, cls_or_name, parent=None):
        super(ConfigDecorator, self).__init__()

        # We create and keep a handle to an instance of the decorated class,
        # because the actual class the user defines (and decorates) will not
        # become a first-class named entity by the Python parser. Instead, the
        # decorator returns an object instance of this class, ConfigDecorator.
        # E.g., in the snippet,
        #   @section
        #   class MyConfig(ConfigDecorator)
        #       pass
        #   obj = MyConfig
        # you'll find that obj is a ConfigDecorator object, and it's not a
        # reference to the MyConfig class. I.e., so you cannot call
        #   # Won't work:
        #   obj = MyConfig()
        # but you can instead (via this attribute) call:
        #   MyConfig._innerobj.foo
        self._innerobj = cls()

        self._parent = parent

        self._kv_cache = OrderedDict()
        self._key_vals = {}

        self._sections = OrderedDict()

        if isinstance(cls_or_name, str):
            self._name = cls_or_name
        else:
            self._name = cls.__name__

        self._pull_kv_cache(parent)

        self._initialized = True

    # ***

    def _pull_kv_cache(self, parent):
        if parent is None:
            return
        # The @decorators run against the parent object.
        # - Fix the settings from the parent cache
        #   to reference this object as the owner.
        for kval in parent._kv_cache.values():
            kval._section = self
        # - Steal its settings cache.
        self._key_vals.update(parent._kv_cache)
        parent._kv_cache = OrderedDict()
        # - Register this object as a section.
        if parent is not self:
            parent._sections[self._name] = self

    # ***

    def _find_root(self):
        if not self._parent:
            return self
        return self._parent._find_root()

    # ***

    def _forget_config_values(self):
        def visitor(condec, keyval):
            keyval.forget_config_value()
        self._walk(visitor)

    # ***

    def _section_path(self, parts=None, sep='_'):
        if parts is None:
            parts = []
        # Ignore the root element. Start with its sections.
        if self._parent is None:
            return sep.join(parts)
        parts.insert(0, self._name)
        return self._parent._section_path(parts, sep)

    # ***

    def _walk(self, visitor):
        for keyval in self._key_vals.values():
            visitor(self, keyval)
        for conf_dcor in self._sections.values():
            conf_dcor._walk(visitor)

    # ***

    def as_dict(self):
        newd = {}
        self.download_to_dict(newd)
        return newd

    def download_to_dict(
        self, config, skip_unset=False, use_defaults=False, add_hidden=False,
    ):
        def _download_to_dict():
            n_settings = 0
            for section, conf_dcor in self._sections.items():
                n_settings += _recurse_section(section, conf_dcor)
            for name, ckv in self._key_vals.items():
                if ckv.ephemeral:
                    continue
                try:
                    config[name] = choose_default_or_confval(ckv)
                    n_settings += 1
                except AttributeError:
                    pass
            return n_settings

        def _recurse_section(section, conf_dcor):
            existed = section in config
            subsect = config.setdefault(section, {})
            n_settings = conf_dcor.download_to_dict(subsect)
            if not n_settings and not existed:
                del config[section]
            return n_settings

        def choose_default_or_confval(ckv):
            if (
                (use_defaults or (not ckv.persisted and not skip_unset))
                and (not ckv.hidden or add_hidden)
            ):
                return ckv.default
            elif not use_defaults and ckv.persisted:
                return ckv.value_from_config
            raise AttributeError()

        return _download_to_dict()

    # ***

    def _update_known(self, config):
        unconsumed = {name: None for name in config.keys()}
        for section, conf_dcor in self._sections.items():
            if section in config:
                unsubsumed = conf_dcor._update_known(config[section])
                if not unsubsumed:
                    del unconsumed[section]
                else:
                    unconsumed[section] = unsubsumed
        for name, ckv in self._key_vals.items():
            if ckv.ephemeral:
                # Essentially unreachable, unless hacked config file.
                continue
            if name in config:
                ckv.value = config[name]
                del unconsumed[name]
        return unconsumed

    # ***

    def _update_gross(self, other):
        # See also, _update_known, which does not add unknown values.
        # This method grabs everything from `other` and shoves it in this
        # ConfigDecorator object. You might find this useful if your app
        # allows self-defined config. E.g., in dob, the user can define
        # their own named styles (that can be referenced in another config).
        # In that instance, the application cannot define the config (key
        # names) ahead of time (using @setting decorators), but instead
        # uses the key names that the user supplies (and calls this method
        # to consume those unknown settings).

        # CAVEAT: (lb): I've only used this method as a shallow update,
        # for flat config (i.e., all values are KeyChainedValue objects,
        # and there are no sections (ConfigDecorator objects)).
        # MAYBE/2019-11-30: (lb): Ensure this handles nested dicts in other,
        # and sets _sections, etc. (For now, you can work around by flattening
        # other and using dotted names to indicate sub-sections, because the
        # setdefault method *is* smart enough to find nested section settings.)
        for key, val in other.items():
            try:
                self[key] = val
            except KeyError:
                self.setdefault(key, val)

    # (lb): We have some dict-ish methods, like setdefault, and keys, values,
    # and items, so might as well have an update method, too. But update is
    # just a shim to _update_gross, so that you're aware there's also the
    # similar method, _update_known. update calls _update_gross, which is
    # more like the actual dict.update() method than _update_known.
    def update(self, other):
        self._update_gross(other)

    # ***

    def setdefault(self, *args):
        # Here we quack like a duck (dict) and supply a smarty pants setdefault,
        # which nark calls to make sure all the config settings it cares about
        # are setup. It's smarty pants because you can use dotted.section.names,
        # and setdefault will descend one or more sections to find the setting.

        def _setdefault():
            _must_args_two_or_more()
            _split_args_on_dot_sep(args[-1], args[:-1])

        def _must_args_two_or_more():
            if len(args) > 1:
                return
            raise TypeError(
                _('setdefault expected at least 2 arguments, got {}')
                .format(len(args))
            )

        def _split_args_on_dot_sep(setting_value, possibly_dotted_names):
            part_names = []
            for name in possibly_dotted_names:
                part_names.extend(name.split('.'))
            setting_name = part_names[-1]
            section_names = part_names[:-1]
            return _setsetting(setting_name, setting_value, *section_names)

        def _setsetting(setting_name, setting_value, *section_names):
            conf_dcor = self
            for section_name in section_names:
                conf_dcor = _getsection(conf_dcor, section_name)
            if setting_name in conf_dcor._key_vals:
                return conf_dcor._key_vals[setting_name]
            ckv = KeyChainedValue(
                name=setting_name,
                default_f=lambda x: setting_value,
                doc=_('Created by `setdefault`'),
                section=self,
            )
            self._key_vals[ckv.name] = ckv
            return setting_value

        def _getsection(conf_dcor, section_name):
            try:
                sub_dcor = conf_dcor._sections[section_name]
            except KeyError:
                # Normally created by the @section decorator,
                # but also by a setdefault, for whyever. (To
                # appease Nark, so it can treat ConfigDecorator
                # like dict of dicts.)
                cls = Subscriptable
                cls_or_name = section_name
                sub_dcor = ConfigDecorator(cls, cls_or_name, parent=conf_dcor)
                conf_dcor._sections[section_name] = sub_dcor
            return sub_dcor

        return _setdefault()

    # ***

    def keys(self):
        # MAYBE/2019-11-30: (lb): What about self._sections??
        return self._key_vals.keys()

    def values(self):
        # MAYBE/2019-11-30: (lb): What about self._sections??
        return [v.value for v in self._key_vals.values()]

    def items(self):
        # MAYBE/2019-11-30: (lb): What about self._sections??
        return {k: v.value for k, v in self._key_vals.items()}

    # ***

    def _find(self, parts, skip_sections=False):
        # If caller specifies just one part, we'll do a loose, lazy match.
        # Otherwise, if parts is more than just one entry, look for exact.
        # - This supports use case of user being lazy, e.g., `dob get tz_aware`,
        #   but also prevents problems being lazy-exact, e.g., `dob get abc xyz`
        #   should be precise and return only abc.xyz, and not, say, zbc.def.xyz.

        def _find_objects():
            if not parts:
                return [self]
            elif len(parts) == 1:
                objects = self._find_objects_named(parts[0], skip_sections)
            else:
                section_names = parts[:-1]
                object_name = parts[-1]

                conf_dcor = self
                for name in section_names:
                    # Raises KeyError if one of the sections not found.
                    conf_dcor = conf_dcor._sections[name]

                objects = []
                if object_name in conf_dcor._sections and not skip_sections:
                    objects.append(conf_dcor._sections[object_name])
                if object_name in conf_dcor._key_vals:
                    objects.append(conf_dcor._key_vals[object_name])

            return objects

        return _find_objects()

    def _find_objects_named(self, name, skip_sections=False):
        objects = []
        if name in self._sections and not skip_sections:
            # Exact section name match.
            objects.append(self._sections[name])
        if name in self._key_vals:
            # Exact setting name match.
            objects.append(self._key_vals[name])
        for section, conf_dcor in self._sections.items():
            # Loosy breadth-first search for name.
            objects.extend(conf_dcor._find_objects_named(name, skip_sections))
        return objects

    def _find_setting(self, parts):
        objects = self._find(parts, skip_sections=True)
        if objects:
            return objects[0]
        return None

    # ***

    def __getattr__(self, name):
        return self._find_one_object(name)

    def __setitem__(self, name, value):
        self._find_one_object(name).value = value

    def _find_one_object(self, name):
        parts = name.split('.')
        if len(parts) > 1:
            # User looked up, e.g., config['section1.section2....key'].
            objects = self._find(parts)
        else:
            objects = self._find_objects_named(name)
        if len(objects) > 1:
            raise KeyError(
                _('More than one config object named: “{}”').format(name)
            )
        if objects:
            return objects[0]
        else:
            # DEV: This happens if you lookup at attr in config you didn't define.
            raise KeyError(
                _('Unrecognized config key: {}.__get__attr__(name="{}")').format(
                    self.__class__.__name__, name,
                )
            )
            return super(ConfigDecorator, self).__getattribute__(name)

    # ***

    # A @redecorator.
    def section(self, name):
        return section(name, parent=self)

    def setting(self, message=None, **kwargs):
        def decorator(func):
            kwargs.setdefault('name', func.__name__)
            doc = message
            if doc is None:
                doc = func.__doc__
            ckv = KeyChainedValue(
                default_f=func,
                doc=doc,
                # self is parent section; we'll set later.
                section=None,
                **kwargs
            )
            self._kv_cache[ckv.name] = ckv

            # EXPLAIN/2019-11-30: (lb): Why not just `return func`?
            def _decorator(*args, **kwargs):
                return func(*args, **kwargs)
            return update_wrapper(_decorator, func)
        return decorator

    # ***


# Note that Python invokes the decorator with the item being decorated. If
# you want to pass arguments to the decorator, you can call a function to
# retain the arguments and to generate the actual decorator .
#
# E.g., if a decorator is not explicitly invoked,
#
#   @section
#   class SomeClass(object):
#       ...
#
# then the argument to the decorator is the SomeClass object. Python executes
# the decorator with the object being decorated, in this case a class.
#
# Otherwise, if a decorator is invoked upon decoration, e.g.,
#
#   @section('SectionName')
#   class SomeClass(object):
#       ...
#
# then the method being invoked must return the actual decorator.
#
# Here we support either approach.

def section(cls_or_name, parent=None):
    def _add_section(cls):
        cfg_dcor = None
        if parent is None or not cls_or_name:
            if parent is not None:
                # The section name is empty, so add settings to the parent.
                # This is useful for using multiple classes to define the
                # settings, but having the settings all added to the same
                # config object. You might do this so you can separate the
                # settings in the code into multiple classes (useful for
                # many reasons, e.g., DRYing code by sharing common methods,
                # or spreading code across multiple files (like plugins)), but
                # also so you can keep the config flat (useful for not making
                # life harder for an end user human that will be editing the
                # flat file config). tl;dr add section to parent.
                cfg_dcor = parent
        elif cls_or_name and cls_or_name in parent._sections:
            # So that two different modules can build the same config,
            #   e.g., in project/myfile1:
            #     @ConfigRoot.section('shared')
            #     class ConfigurableA(Subscriptable):
            #         ...
            #   then in project/myfile2:
            #     @ConfigRoot.section('shared')
            #     class ConfigurableB(Subscriptable):
            #         ...
            # and also for the reasons listed in the long previous comment,
            # return the named section if previously defined.
            cfg_dcor = parent._sections[cls_or_name]

        if cfg_dcor is None:
            # The constructor calls _pull_kv_cache if parent is not None.
            cfg_dcor = ConfigDecorator(cls, cls_or_name, parent=parent)

        # For calling _pull_kv_cache, have parent be self, so
        # one can add settings to the root config object.
        cfg_dcor._pull_kv_cache(parent or cfg_dcor)

        return cfg_dcor

    # Check if decorator was @gentle or @explicit().
    if inspect.isclass(cls_or_name):
        # The decorator was used without being invoked first, e.g.,
        #   @section
        #   class Classy...
        _add_section(cls_or_name)
        return cls_or_name
    else:
        # The decorator was invoked first with arguments, so return the
        # actual decorator which Python will call back immediately with
        # the class being decorated.
        return _add_section

