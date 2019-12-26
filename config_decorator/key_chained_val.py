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
"""Defines a class to manage a key-value setting.
"""

from __future__ import absolute_import, unicode_literals

from gettext import gettext as _

import os

__all__ = (
    'KeyChainedValue',
)


class KeyChainedValue(object):
    """Represents one setting of a section of a hierarchical settings configuration.

    .. automethod:: __init__
    """

    _envvar_prefix = ''

    def __init__(
        self,
        section=None,
        name='',
        default_f=None,
        value_type=None,
        allow_none=False,
        # Optional.
        choices='',
        doc='',
        ephemeral=False,
        hidden=False,
        validate=None,
    ):
        """Inits a :class:`KeyChainedValue` object.

        Do not create these objects directly, but instead
        use the
        :func:`config_decorator.config_decorator.ConfigDecorator.settings`
        decorator.

        Except for ``section``, the following arguments may be specified
        in the decorator call.

        For instance::

            @property
            @RootSectionBar.setting(
                "An example setting.",
                name='foo-bar',
                value_type=bool,
                hidden=True,
                # etc.
            )
            def foo_bar(self):
                return 'True'

        Args:
            section: A reference to the section that contains this setting
                     (a :class:`config_decorator.config_decorator.ConfigDecorator`).
            name: The setting name, either inferred from the class method that
                  is decorated, or specified explicitly.
            default_f: A method (i.e., the decorated class method)
                       that generates the default setting value.
            value_type: The setting type, either inferred from the type of
                        the default value, or explicitly indicated.
                        It's often useful to explicitly set ``bool`` types
                        so that the default function can return a ``'True'``
                        or ``'False'`` string.
            allow_none: True if the value is allowed to be ``None``, otherwise
                        when the value is set, it will be passed to the type
                        converted, which might fail on None, or produce
                        unexpected results
                        (such as converting ``None`` to ``'None'``).
            choices: A optional list of valid values, used to validate input
                     when setting the value.
            doc: Helpful text about the setting, which your application could
                 use to show the user. The ``doc`` can specified as a keyword
                 argument, or as the first positional argument to the decorator.
            ephemeral: If True, the setting is meant not to be persisted
                       between sessions (e.g., ``ephemeral`` settings are
                       excluded on a call to
                       :meth:`config_decorator.config_decorator.ConfigDecorator.download_to_dict`
                       .)
            hidden: If True, the setting is excluded from an output operation
                    if the value is the same as the setting's default value.
            validate: An optional function to validate the value when set
                      from user input. If the validate function returns a
                      falsey value, setting the value raises ``ValueError``.
        """
        self._section = section
        self._name = name
        self._default_f = default_f
        self._choices = choices
        self._doc = doc
        self._ephemeral = ephemeral
        self._hidden = hidden
        self._validate_f = validate

        self._value_type = self._deduce_value_type(value_type)
        self._value_allow_none = allow_none

        # These attributes will only be set if some particular
        # source specifies a value:
        #  self._val_forced
        #  self._val_cliarg
        #  self._val_envvar
        #  self._val_config

    @property
    def name(self):
        """Returns the setting name.
        """
        return self._name

    @property
    def default(self):
        """Returns the default setting value.
        """
        return self._default_f(self._section)

    def _deduce_value_type(self, value_type=None):
        if value_type is not None:
            return value_type
        elif self.ephemeral:
            return lambda val: val
        return self._deduce_default_type()

    def _deduce_default_type(self):
        default_value = self.default
        if default_value is None:
            return lambda val: val
        elif isinstance(default_value, bool):
            return bool
        elif isinstance(default_value, int):
            return int
        elif isinstance(default_value, list):
            # Because ConfigObj auto-detects list-like values,
            # we might get a string value in a list-type setting,
            # which we don't want to ['s', 'p', 'l', 'i', 't'].
            # So rather than a blind:
            #   return list
            # we gotta be smarter.
            return self._typify_list
        elif isinstance(default_value, str):
            return str
        # We could default to, say, str, or we could nag user to either
        # add another `elif` here, or to fix their default return value.
        raise NotImplementedError

    @property
    def doc(self):
        """Returns the setting help text.
        """
        return self._doc

    @property
    def ephemeral(self):
        """Returns the ephemeral state.
        """
        if callable(self._ephemeral):
            if self._section is None:
                return False
            return self._ephemeral(self)
        return self._ephemeral

    def find_root(self):
        """Returns the topmost section object."""
        # (lb): This function probably not useful, but offered as parity
        # to what's in ConfigDecorator. And who knows, maybe a developer
        # will find useful from a debug prompt.
        return self._section.find_root()

    @property
    def hidden(self):
        """Returns the hidden state.
        """
        if callable(self._hidden):
            if self._section is None:
                # FIXME/2019-12-23: (lb): I think this is unreachable,
                # because self._section is only None when config is
                # being built, but hidden not called during that time.
                return False
            return self._hidden(self)
        return self._hidden

    @property
    def persisted(self):
        """Returns True if the setting value was set via :meth:`value_from_config`.
        """
        return hasattr(self, '_val_config')

    def _typify(self, value):
        if self._value_allow_none and value is None:
            return value
        if self._value_type is bool:
            if isinstance(value, bool):
                return value
            elif value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                raise ValueError(
                    _("Unrecognized string for bool setting ‘{}’: “{}”").format(
                        self._name, value,
                    ),
                )
        return self._value_type(value)

    def _typify_list(self, value):
        # Handle ConfigObj parsing a string without finding commas to
        # split on, but the @setting indicating it's a list; or a
        # default method returning [] so we avoid calling list([]).
        if isinstance(value, list):
            return value
        return [value]

    def walk(self, visitor):
        visitor(self._section, self)

    # ***

    @property
    def value(self):
        """Returns the setting value read from the highest priority source.

        Returns:

            The setting value from the highest priority source,
            as determined by the order of this list:

            - If the setting value was forced,
              by a call to the :meth:`value_from_forced` setter,
              that value is returned.

            - If the setting value was read from a command line argument,
              by a call to the :meth:`value_from_cliarg` setter,
              that value is returned.

            - If the setting value was read from an environment variable,
              by a call to the :meth:`value_from_envvar` setter,
              that value is returned.

            - If the setting value was read from the dictionary source,
              by a call to the :meth:`value` or :meth:`value_from_config` setters,
              that value is returned.

            - Finally, if a value was not obtained from any of the above
              sources, the default value is returned.
        """
        # Honor forced values foremost.
        try:
            return self.value_from_forced
        except AttributeError:
            pass
        # Honor CLI-specific values secondmost.
        try:
            return self.value_from_cliarg
        except AttributeError:
            pass
        # Check the environment third.
        try:
            return self.value_from_envvar
        except KeyError:
            pass
        # See if the config value was specified by the config that was read.
        try:
            return self.value_from_config
        except AttributeError:
            pass
        # Nothing found so far! Finally just return the default value.
        return self._typify(self.default)

    @value.setter
    def value(self, value):
        """Sets the setting value to the value supplied.

        Args:
            value: The new setting value.
                   The value is assumed to be from the config,
                   i.e., this method is an alias to
                   the :meth:`value_from_config` setter.
        """
        value = self._value_cast_and_validate(value)
        # Using the `value =` shortcut, or using `section['key'] = `,
        # is provided as a convenient way to inject values from the
        # config file, or that the user wishes to set in the file.
        # If the caller wants to just override the value, consider
        # setting self.value_from_forced instead.
        self.value_from_config = value

    def _value_cast_and_validate(self, value):
        value = self._typify(value)
        invalid = False
        addendum = ''
        if self._validate_f:
            if not self._validate_f(value):
                invalid = True
        elif self._choices:
            if value not in self._choices:
                invalid = True
                addendum = _(' (Choose from: ‘{}’)').format('’, ‘'.join(self._choices))
        if invalid:
            raise ValueError(
                _("Unrecognized value for setting ‘{}’: “{}”{}").format(
                    self._name, value, addendum,
                ),
            )
        return value

    # ***

    @property
    def value_from_forced(self):
        """Returns the "forced" setting value.
        """
        return self._val_forced

    @value_from_forced.setter
    def value_from_forced(self, value_from_forced):
        """Sets the "forced" setting value, which supersedes values from all other sources.

        Args:
            value_from_forced: The forced setting value.
        """
        self._val_forced = self._typify(value_from_forced)

    # ***

    @property
    def value_from_cliarg(self):
        """Returns the "cliarg" setting value.
        """
        return self._val_cliarg

    @value_from_cliarg.setter
    def value_from_cliarg(self, value_from_cliarg):
        """Sets the "cliarg" setting value, which supersedes the envvar, config, and default values.

        Args:
            value_from_cliarg: The forced setting value.
        """
        self._val_cliarg = self._typify(value_from_cliarg)

    # ***

    @property
    def value_from_envvar(self):
        """Returns the "envvar" setting value, sourced from the environment when called.

        A name derived from a special prefix, the section path,
        and the setting name is used to look for an environment
        variable of the same name.

        For example, consider that an application use the prefix
        "CFGDEC\\_", and the setting is under a subsection called
        "pokey" which is under a topmost section called "hokey".
        If the setting is named "foot",
        then the environment variable would be named,
        "CFGDEC_HOKEY_POKEY_FOOT".
        """
        environame = '{}{}_{}'.format(
            KeyChainedValue._envvar_prefix,
            self._section.section_path(sep='_').upper(),
            self._name.upper(),
        )
        envval = os.environ[environame]
        envval = self._value_cast_and_validate(envval)
        return envval

    # ***

    @property
    def value_from_config(self):
        """Returns the "config" setting value.
        """
        return self._val_config

    @value_from_config.setter
    def value_from_config(self, value_from_config):
        """Sets the "config" setting value, which supersedes the default value.

        Args:
            value_from_config: The forced setting value.
        """
        self._val_config = self._typify(value_from_config)

    def forget_config_value(self):
        """Removes the "config" setting value set by the :meth:`value_from_config` setter.
        """
        try:
            del self._val_config
        except AttributeError:
            pass

    @property
    def asobj(self):
        """Returns self, behaving as identify function (need to quack like ``ConfigDecorator``).
        """
        return self


