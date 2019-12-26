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
"""Class @decorator for defining exquisite settings configurations.

Concepts
--------

A configurable setting is some value in an application that can be
"globally" set.

Most often, a configurable setting is used so that an end user can
change the behavior of an application. All settings might be saved
to a file on disk and read whenever the application starts. In this
case, the collection of configurable settings might simply be called
the "user options".

But you could also use configurable settings to decouple code. For
example, rather than two objects sharing values by interacting with
one another, they could instead share values using a common settings
configuration. Then the two objects only need to know common key names,
and not about each other.

At its core, each setting has a name (its key), and a value. The value could
be a default value specified in code, or it could be a value somehow specified
by the user, such as from the command line, or from an environment variable,
or from a file saved on disk.

Furthermore, each setting has a description (some helpful text),
a type (int, bool, list, etc.),
an optional validation function,
and other qualities
(see more in the ``key_chained_val`` module).

Multiple settings can be organized into
hierarchically-related groups, or sections
(as represented by the :class:`ConfigDecorator` class,
but generated using the ``@section`` decorator).

In addition to settings, each section may also contain sections
(or, more aptly, *subsections*).

You can think of the complete hierarchical collection of sections and
their settings as a *settings configuration*, or as the *user options*.

Each section of a settings configuration is represented by a
:class:`ConfigDecorator` instance. The settings themselves are
each represented by a ``KeyChainedVal`` instance.

Typical usage
-------------

To create a settings configuration, use the ``@section`` decorator
once to designate the root object of the settings configuration.
The decorated class is then used to decorate each subsection class,
as well as each settings method. (And then the subsection classes can
be used to decorate sub-subsections and their settings, and so on.)

For example::

    def generate_config(self):
        '''An example setting configuration generator.'''

        @section(None)
        class RootSection(object):
            pass

        @RootSection.section('foo')
        class RootSectionFoo(object):
            def __init__(self):
                pass

        @RootSection.section('bar')
        class RootSectionBar(object):
            def __init__(self):
                pass

        @RootSectionBar.section('baz')
        class BarSubsectionBaz(object):
            def __init__(self):
                pass

            @property
            @RootSectionBar.setting(
                "An example setting.",
            )
            def bat(self):
                return 'Ta-Da!'

        return RootSection

In the example above, there are two root sections defined, "foo" and "bar".
And there's one setting defined in the "bar.baz" subsection. You could run,
e.g.,::

    >>> cfg = generate_config()
    >>> cfg.bar.baz.bat
    'Ta-Da!'

Note that because of how decorators operate on a class (they execute
after the class is defined), the settings defined in a class definition
must be decoratored using that class's parent section. (In the previous
example, ``@RootSectionBar.setting`` was used inside ``BarSubsectionBaz``.)

.. Important::

  - You cannot access the decorated user class using its name.

    - The ``@section`` decorator wraps the class definition in a
      :class:`ConfigDecorator` instance, and it returns that object.

    - So in the previous example,
      ``RootSection`` is a :class:`ConfigDecorator` instance
      and not a ``class`` object.
      I.e., you cannot call ``obj = RootSection()``.
"""

from __future__ import absolute_import, unicode_literals

import inspect
from collections import OrderedDict
from functools import update_wrapper

from gettext import gettext as _

from .key_chained_val import KeyChainedValue

__all__ = (
    # So that the Sphinx docs do not generate help on the `section`
    # function twice (because __init__.py creates an alias to it),
    # do not export said function from this module.
    #   'section',
    # (lb): The ConfigDecorator is technically private, because the user
    # calls @section() and doesn't make ConfigDecorator objects directly.
    # However, not including the class in __all__ excludes it from docs/, too.
    'ConfigDecorator',
)


class ConfigDecorator(object):
    """Represents one section of a hierarchical settings configuration.

    A settings configuration is a collection of user-settable key-value
    settings grouped and organized into a tree-like graph of sections.

    A settings configuration has one root section, which may have any number
    of subsections and settings therein. Each subsection may also contain
    any number of subsections and settings.

    Each :class:`ConfigDecorator` wraps a user class that defines
    the settings in that section.
    To add subsections to a section, use the section object's
    :func:`ConfigDecorator.section` decorator.
    One or more classes are defined and decorated this way
    to build a hierarchical settings configuration.

    .. Important::

        Users of this library do not call :class:`ConfigDecorator()` directly.

        Rather, object creation is handled by the
        :meth:`config_decorator.section` and
        :func:`ConfigDecorator.section`
        decorators.

    Args:
        cls: The class being decorated.
        cls_or_name: The section name to use in the settings configuration.
        parent: A reference to the parent section
                (a :class:`ConfigDecorator` object),
                or ``None`` for the root section.

    Attributes:
        _innercls: The class object that was decorated
                   (whose name now references a :class:`ConfigDecorator` instance,
                   and not the :class:`class` object that was defined.
        _innerobj: An instance of the class object that was decorated.
        _parent: A reference to the parent :class:`ConfigDecorator` section,
                 or ``None`` for the root section.
        _kv_cache: An ordered dict of settings defined by the class,
                   used internally when build the settings configuration
                   (i.e., used internally while sourcing Python code).
        _key_vals: This section's settings, stored as a dict
                   (setting name ⇒
                   :class:`config_decorator.key_chained_val.KeyChainedValue` object).
        _sections: An ordered dict of subsections
                   (section name ⇒ :class:`ConfigDecorator` object).
        _name: The section name, specified in the decorator,
               or inferred from the class name.

    .. DEV: Use `automethod` to document private functions (include them in docs/_build).
    ..
    .. E.g., `automethod:: _my_method_name`
    """

    SEP = '.'
    """Separator character used to (un)flatten section.subsection.settings paths."""

    def __init__(self, cls, cls_or_name, parent=None):
        """Inits ConfigDecorator with class being decorated, section name, and optional parent reference.
        """
        # (lb): Note that `make docs` ignores the __init__ docstring;
        # it shows the params in the class docstring, though, so the
        # parameters are documented there.

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
        #   obj.foo
        # but you can instead call:
        #   MyConfig._innerobj.foo
        self._innercls = cls
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

    # ***

    def _pull_kv_cache(self, parent):
        """Consumes the accumulated settings cache from the parent section.

        Because the decorator is not called until after the class it
        decorates is defined, and because we want the user to be able
        to decorate the methods within the class being decorated, the
        method decorates must register the settings with the parent section
        instead. Then, when the decorated is called once the class is defined,
        we snatch the settings back from the parent's cache.
        """
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

    def find_root(self):
        """Returns the topmost section object, that which has no parent."""
        if not self._parent:
            return self
        return self._parent.find_root()

    # ***

    def forget_config_values(self):
        """Visits every setting and removes the value from the "config" source.

        Unless a setting's value can be gleaned from an environment variable,
        or was parsed from the command line, or was forceable set by the code,
        calling this method will effectively set the value back to its default.
        """
        def visitor(condec, keyval):
            keyval.forget_config_value()
        self.walk(visitor)

    # ***

    def section_path(self, sep=None, _parts=None):
        """Returns a flattened canonicalized representation of the complete section path.

        Args:
            sep: The separator character to use, defaults to ConfigDecorator.SEP.
            _parts: Used internally on recursive calls to this function.

        Returns:
            The "path" to this section, as derived from the name of the root
            section on downward to this section, using the separator character
            between each successive section's name.
        """
        if _parts is None:
            _parts = []
        if sep is None:
            sep = self.SEP
        # Ignore the root element. Start with its sections.
        if self._parent is None:
            return sep.join(_parts)
        _parts.insert(0, self._name)
        return self._parent.section_path(sep, _parts)

    # ***

    def walk(self, visitor):
        """Visits every section and runs the passed method on every setting.

        Args:
            visitor: Function to run on each setting.
                     Will be passed a reference to the :class:`ConfigDecorator`,
                     and a reference to the
                     :class:`config_decorator.key_chained_val.KeyChainedValue` object.
        """
        for keyval in self._key_vals.values():
            visitor(self, keyval)
        for conf_dcor in self._sections.values():
            conf_dcor.walk(visitor)

    # ***

    def as_dict(self):
        """Returns a new dict representing the configuration settings tree.
        """
        newd = {}
        self.download_to_dict(newd)
        return newd

    def download_to_dict(
        self, config, skip_unset=False, use_defaults=False, add_hidden=False,
    ):
        """Updates the passed dict with all configuration settings.

        Args:
            config: The dict to update.
            skip_unset: Set True to exclude settings that do not have a value
                        set from the "config" source.
            use_defaults: Set True to use the default value for every setting.
            add_hidden: Set True to include settings with the "hidden" property set.

        Returns:
            The number of settings updated or added to the "config" dict.
        """
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

    def update_known(self, config):
        """Updates existing settings values from a given dictionary.

        Args:
            config: A dict whose key-values will be used to set
                    settings "config" value sources accordingly.

        Returns:
            A dict containing any unknown key-values from "config"
            that did not correspond to a known section or setting.
        """
        unconsumed = {name: None for name in config.keys()}
        for section, conf_dcor in self._sections.items():
            if section in config:
                unsubsumed = conf_dcor.update_known(config[section])
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

    def update_gross(self, other):
        """Consumes all values from a dict, creating new sections and settings as necessary.

        Args:
            other: The dict whose contents will be consumed.

        See also :meth:`update_known`, which does not add unknown values.

        This method is less discerning. It grabs everything from ``other``
        and shoves it in the ConfigDecorator object, creating section
        and setting objects as necessary.

        You might find this useful if your app handles arbitrary config.
        In this case, the application cannot define the config in the code,
        because it lets the user use whatever names they want. In that case,
        load the config into a dict (say, using |ConfigObj|_), and then pass
        that dictionary to this method.

        .. |ConfigObj| replace:: ``ConfigObj``
        .. _ConfigObj: https://github.com/DiffSK/configobj
        """
        # For instance, the ``dob`` application allows the user to define their
        #   own named Pygment styles that can be referenced in a separate config.
        #   Because of this, the application cannot define the config ahead of
        #   time (using @setting decorators) because it does not know the setting
        #   names (which are whatever the user wants)
        # CAVEAT: (lb): I've only used this method as a shallow update, for flat
        #   config (i.e., all values are KeyChainedValue objects, and there are no
        #   sections (ConfigDecorator objects)).
        #   - MAYBE/2019-11-30: (lb): Ensure this handles nested dicts in other,
        #     and sets _sections, etc. (For now, you can work around by flattening
        #     other and using dotted names to indicate sub-sections, because the
        #     setdefault method *is* smart enough to find nested section settings.)
        for key, val in other.items():
            try:
                self[key] = val
            except KeyError:
                self.setdefault(key, val)

    # (lb): We have some dict-ish methods, like setdefault, and keys, values,
    # and items, so might as well have an update method, too. But update is
    # just a shim to update_gross, so that you're aware there's also the
    # similar method, update_known. update calls update_gross, which is
    # more like the actual dict.update() method than update_known.
    def update(self, other):
        """Alias to :meth:`update_gross`.
        """
        self.update_gross(other)

    # ***

    def setdefault(self, *args):
        """Ensures the indicated setting exists, much like ``dict.setdefault``.

        Args:
            args: one or more arguments indicating the section path and setting name,
                  and one final argument indicating the default setting value to use.

        Returns:
            The setting value (the existing value if already set; otherwise
            the new default value, which is also the last item in ``*args``).
        """
        # Here we quack like a duck (dict) and supply a smarty pants setdefault, which
        # the nark package calls to make sure all the config settings it cares about
        # are setup. It's smarty pants because you can use dotted.section.names, and
        # setdefault will descend one or more sections to find the setting.

        def _setdefault():
            must_args_two_or_more()
            return split_args_on_dot_sep(args[-1], args[:-1])

        def must_args_two_or_more():
            if len(args) > 1:
                return
            raise TypeError(
                _('setdefault expected at least 2 arguments, got {}')
                .format(len(args))
            )

        def split_args_on_dot_sep(setting_value, possibly_dotted_names):
            part_names = []
            for name in possibly_dotted_names:
                part_names.extend(name.split(self.SEP))
            setting_name = part_names[-1]
            section_names = part_names[:-1]
            return setsetting(setting_name, setting_value, *section_names)

        def setsetting(setting_name, setting_value, *section_names):
            conf_dcor = self
            for section_name in section_names:
                conf_dcor = getsection(conf_dcor, section_name)
            if setting_name in conf_dcor._key_vals:
                # Unlike the method name might imply (set-DEFAULT), we don't
                # actually set the KeyChainedValue default. We simple ensure
                # that the setting exists. (The method is called "setdefault"
                # to indicate its similarity to Python's ``dict.setdefault``.)
                return conf_dcor._key_vals[setting_name]
            ckv = KeyChainedValue(
                name=setting_name,
                default_f=lambda x: setting_value,
                doc=_('Created by `setdefault`'),
                section=self,
            )
            self._key_vals[ckv.name] = ckv
            return setting_value

        def getsection(conf_dcor, section_name):
            try:
                sub_dcor = conf_dcor._sections[section_name]
            except KeyError:
                # Normally created by the @section decorator,
                # but also by a setdefault, for whyever. (To
                # appease Nark, so it can treat ConfigDecorator
                # like dict of dicts.)
                cls = object
                cls_or_name = section_name
                sub_dcor = ConfigDecorator(cls, cls_or_name, parent=conf_dcor)
                conf_dcor._sections[section_name] = sub_dcor
            return sub_dcor

        return _setdefault()

    # ***

    def keys(self):
        """Returns a list of settings names.
        """
        # MAYBE/2019-11-30: (lb): What about self._sections??
        return self._key_vals.keys()

    def values(self):
        """Returns a list of settings values.
        """
        # MAYBE/2019-11-30: (lb): What about self._sections??
        return [v.value for v in self._key_vals.values()]

    def items(self):
        """Returns a dictionary of setting key names → values.
        """
        # MAYBE/2019-11-30: (lb): What about self._sections??
        return {k: v.value for k, v in self._key_vals.items()}

    # ***

    def find_all(self, parts, skip_sections=False):
        """Returns all matching sections or settings.

        Args:
            parts: A list of strings used to find matching sections and settings.

                   - If empty, the currect section is returned (the identify function).

                   - If just one name is specified in "parts", all sections and
                     settings that match that name are assembled and returned
                     (by performing a breadth-first search of the current section
                     and its subsections).

                   - If more than one name is specified, the leading names are used to
                     form the path to the section to search; and then any section or
                     setting in that section matching the final name in "parts" is returned.

            skip_sections: If True, do not include section objects in the results.

        Returns:
            A list of matching sections and settings.
        """
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

    def find_setting(self, parts):
        """Returns the setting with the given path and name.

        Args:
            parts: A list of strings indicating the section names and setting name.

        Returns:
            The indentified setting, or None if no setting found.
        """
        objects = self.find_all(parts, skip_sections=True)
        if objects:
            return objects[0]
        return None

    # ***

    @property
    def asobj(self):
        """Returns a representation of the section that can be accessed like an object.

        Returns:

            An object that overrides ``__getattr__`` to find the section or setting
            in the current section that has the given name.

            The object also has a magic ``_`` method, if you want to use dot-notation
            to get at a subsection, but then want access to the actual section object.
        """
        class anyobj(object):
            def __getattr__(_self, name):
                # See also:
                #   return super(ConfigDecorator, self).__getattribute__(name)
                return self._find_one_object(name, AttributeError, asobj=True)
            @property
            def _(_self):
                """A wonky get-out-of-jail-free card, or reference to the section.
                """
                return self
        return anyobj()

    def __getitem__(self, name):
        """Returns the section or setting with the given name.

        Makes an otherwise non-subscriptable object subscriptable.

           I.e., calling ``obj['key']`` maps to ``obj.key``.

           Or, put another way, the user can access data at *obj['key']* as well as *obj.key*.

        .. Note::

            If the derived class has a ``value`` attribute, that attribute
            is returned instead.

            E.g., given a ``ConfigDecorator`` settings configuration,
            you can call either ``cfg['foo']['bar']`` or more
            simply ``cfg.foo.bar.value``.

        Args:
            name: Attribute name to lookup.

        Raise:
            AttributeError
        """
        item = self._find_one_object(name, AttributeError)
        try:
            return item.value
        except AttributeError:
            return item

    def __setitem__(self, name, value):
        self._find_one_object(name, KeyError).value = value

    def _find_one_object(self, name, error_cls, asobj=False):
        parts = name.split(self.SEP)
        if len(parts) > 1:
            # User looked up, e.g., config['section1.section2....key'].
            objects = self.find_all(parts)
        else:
            objects = self._find_objects_named(name)
        if len(objects) > 1:
            raise error_cls(
                _('More than one config object named: “{}”').format(name)
            )
        if objects:
            return objects[0].asobj if asobj else objects[0]
        else:
            # DEV: This happens if you lookup an attr in config you didn't define.
            raise error_cls(
                _('Unknown section for {}.__getattr__(name="{}")').format(
                    self.__class__.__name__, name,
                )
            )

    # ***

    # A @redecorator.
    def section(self, name):
        """Class decorator used to create subsections.

        For instance::

            @section(None)
            class RootSection(object):
                pass

            @RootSection.section('My Subsection')
            class MySubsection(object):
                pass

            @MySubsection.section('A Grandsubsection')
            class AGrandsubsection(object):
                pass

        Args:
            name: The name of the subsection.

        Returns:
            A :class:`ConfigDecorator` instance.

        See :func:`config_decorator.config_decorator.section`
        :func:`section`
        for a more complete explanation.
        """
        return section(name, parent=self)

    def setting(self, message=None, **kwargs):
        """Method decorator used to create individual settings in a configuration section.

        For instance::

            ...

            @RootSection.section('My Subsection')
            class MySubsection(object):
                @property
                @RootSection.setting(
                    "An example setting.",
                    name="my-setting"
                )
                def my_setting(self):
                    return 'My Setting's Default Value'

        """
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
                # FIXME/2019-12-23: (lb): This might be unreachable code.
                return func(*args, **kwargs)
            return update_wrapper(_decorator, func)
        return decorator

    # ***


# Note that Python invokes the decorator with the item being decorated. If
# you want to pass arguments to the decorator, you can call a function to
# retain the arguments and to generate the actual decorator.
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
    """Class decorator used to indicate the root section of a settings configuration.

    For instance::

        @section(None)
        class RootSection(object):
            pass

    See :ref:`Concepts` for more help and usage examples.

    Args:
        cls_or_name: The section name, or the class being decorated
                     if the decorator was not closed.
        parent: When defining a subsection, the reference to the parent section
                (used internally by
                :meth:`config_decorator.config_decorator.ConfigDecorator.section`).

    Returns:
        A :class:`ConfigDecorator` instance.

        .. Important::

          The name of the decorated class does not reference the defined user
          class, but rather it's a
          :class:`config_decorator.config_decorator.ConfigDecorator`
          instance.

          To access the class definition that was decorated,
          use the return object's ``_innercls`` attribute.

          To access an instance of the decorated class, use ``_innerobj``.
    """
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
            #     class ConfigurableA(object):
            #         ...
            #   then in project/myfile2:
            #     @ConfigRoot.section('shared')
            #     class ConfigurableB(object):
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

