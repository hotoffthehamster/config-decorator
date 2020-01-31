# This file exists within 'config-decorator':
#
#   https://github.com/hotoffthehamster/config-decorator
#
# Copyright © 2019-2020 Landon Bouma. All rights reserved.
#
# Permission is hereby granted,  free of charge,  to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge,  publish,  distribute, sublicense,
# and/or  sell copies  of the Software,  and to permit persons  to whom the
# Software  is  furnished  to do so,  subject  to  the following conditions:
#
# The  above  copyright  notice  and  this  permission  notice  shall  be
# included  in  all  copies  or  substantial  portions  of  the  Software.
#
# THE  SOFTWARE  IS  PROVIDED  "AS IS",  WITHOUT  WARRANTY  OF ANY KIND,
# EXPRESS OR IMPLIED,  INCLUDING  BUT NOT LIMITED  TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE  FOR ANY
# CLAIM,  DAMAGES OR OTHER LIABILITY,  WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE,  ARISING FROM,  OUT OF  OR IN  CONNECTION WITH THE
# SOFTWARE   OR   THE   USE   OR   OTHER   DEALINGS  IN   THE  SOFTWARE.

"""Class to manage key-value settings."""

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
        conform=None,
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
                       :meth:`config_decorator.config_decorator.ConfigDecorator.apply_items`
                       .)
            hidden: If True, the setting is excluded from an output operation
                    if the value is the same as the setting's default value.
            validate: An optional function to validate the value when set
                      from user input. If the validate function returns a
                      falsey value, setting the value raises ``ValueError``.
            conform: If set, function used to translate config value to
                           value used internally. Useful for datetime, etc.
        """
        self._section = section
        self._name = name
        self._default_f = default_f
        self._choices = choices
        self._doc = doc
        self._ephemeral = ephemeral
        self._hidden = hidden
        self._validate_f = validate
        self._conform_f = conform

        self._value_allow_none = allow_none
        self._value_type = self._deduce_value_type(value_type)

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
            # Caller can specify, say, a function to do type conversion,
            # but they're encouraged to stick to builtin types, and to
            # use `conform` if they need to change values on input.
            return value_type
        elif self.ephemeral:
            return lambda val: val
        return self._deduce_default_type()

    def _deduce_default_type(self):
        default_value = self.default
        if default_value is None:
            # If user wrote default method to return None, then obviously
            # implicitly the setting allows the None value.
            self._value_allow_none = True
            # Furthermore, the value type is implicitly whatever, because
            # the user did not specify the type of None that is the default.
            # So rather than assume, the type function is just the identity.
            # (The user cat set value_type to be explicit about the type.
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
        msg = _(' (Unrecognized value type: ‘{}’)').format(
            type(default_value).__name__,
        )
        raise NotImplementedError(msg)

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
        if value is None:
            if self._value_allow_none:
                return value
            raise ValueError(_(" (No “None” values allowed)"))
        if self._value_type is bool:
            if isinstance(value, bool):
                return value
            elif value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                raise ValueError(_(" (Expected a bool, or “True” or “False”)"))
        try:
            value = self._value_type(value)
        except Exception as err:
            raise ValueError(_(" ({})").format(str(err)))
        return value

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

    def __str__(self):
        return '{}{}{}: {}'.format(
            self._section.section_path(),
            self._section.SEP,
            self._name,
            self.value,
        )

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
        return self._value_conform_and_validate(self.default)

    @value.setter
    def value(self, value):
        """Sets the setting value to the value supplied.

        Args:
            value: The new setting value.
                   The value is assumed to be from the config,
                   i.e., this method is an alias to
                   the :meth:`value_from_config` setter.
        """
        orig_value = value
        value = self._value_conform_and_validate(value)
        # Using the `value =` shortcut, or using `section['key'] = `,
        # is provided as a convenient way to inject values from the
        # config file, or that the user wishes to set in the file.
        # Don't call the wrapper, which would call conform-validate again.
        #   NOPE: self.value_from_config = value
        self._val_config = value
        self._val_origin = orig_value

    def _value_conform_and_validate(self, value):

        def _corformidate():
            _value = value
            addendum = None
            if addendum is None:
                addendum = _validate(_value)
            if addendum is None:
                try:
                    _value = _typify_and_conform(_value)
                except Exception as err:
                    addendum = str(err)
            if addendum is not None:
                raise ValueError(
                    _("Unrecognized value for setting ‘{}’: “{}”{}").format(
                        self._name, value, addendum,
                    ),
                )
            return _value

        def _typify_and_conform(_value):
            _value = self._typify(value)
            if self._conform_f:
                _value = self._conform_f(_value)
            return _value

        def _validate(_value):
            # Returns None if valid value, or string if it's not.
            addendum = None
            if self._validate_f:
                try:
                    # The caller's validate will either raise or return a truthy.
                    if not self._validate_f(_value):
                        addendum = ''
                except Exception as err:
                    addendum = str(err)
            elif self._choices:
                if _value not in self._choices:
                    addendum = _(' (Choose from: ‘{}’)').format(
                        '’, ‘'.join(self._choices)
                    )
            return addendum

        return _corformidate()

    # ***

    @property
    def value_from_default(self):
        """Returns the conformed default value.
        """
        return self._value_conform_and_validate(self.default)

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
        self._val_forced = self._value_conform_and_validate(value_from_forced)

    # ***

    @property
    def value_from_cliarg(self):
        """Returns the "cliarg" setting value.
        """
        return self._val_cliarg

    @value_from_cliarg.setter
    def value_from_cliarg(self, value_from_cliarg):
        """Sets "cliarg" setting value, which supersedes envvar, config, and default.

        Args:
            value_from_cliarg: The forced setting value.
        """
        self._val_cliarg = self._value_conform_and_validate(value_from_cliarg)

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
        envval = self._value_conform_and_validate(envval)
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
        orig_value = value_from_config
        self._val_config = self._value_conform_and_validate(value_from_config)
        self._val_origin = orig_value

    def forget_config_value(self):
        """Removes the "config" setting value set by the :meth:`value_from_config` setter.
        """
        try:
            del self._val_config
        except AttributeError:
            pass

    # ***

    @property
    def value_unmutated(self):
        """Returns the storable config value, generally just the stringified value."""
        try:
            # Prefer the config value as original input, i.e., try to keep
            # the output same as user's input. But still cast to string.
            # Mostly just avoid whatever self.conform_f may have done.
            return str(self._val_origin)
        except AttributeError:
            # No config value set, so stringify the most prominent value.
            return str(self.value)

    # ***

    @property
    def asobj(self):
        """Returns self, behaving as identify function (need to quack like ``ConfigDecorator``).
        """
        return self

    # ***

    @property
    def source(self):
        """Returns the setting value source.

        Returns:

            The name of the highest priority source,
            as determined by the order of this list:

            - If the setting value was forced,
              by a call to the :meth:`value_from_forced` setter,
              the value 'forced' is returned.

            - If the setting value was read from a command line argument,
              by a call to the :meth:`value_from_cliarg` setter,
              the value 'cliarg' is returned.

            - If the setting value was read from an environment variable,
              by a call to the :meth:`value_from_envvar` setter,
              the value 'envvar' is returned.

            - If the setting value was read from the dictionary source,
              by a call to the :meth:`value` or :meth:`value_from_config` setters,
              the value 'config' is returned.

            - Finally, if a value was not obtained from any of the above
              sources, the value 'default' is returned.
        """
        # Honor forced values foremost.
        try:
            return self.value_from_forced and 'forced'
        except AttributeError:
            pass
        # Honor CLI-specific values secondmost.
        try:
            return self.value_from_cliarg and 'cliarg'
        except AttributeError:
            pass
        # Check the environment third.
        try:
            return self.value_from_envvar and 'envvar'
        except KeyError:
            pass
        # See if the config value was specified by the config that was read.
        try:
            return self.value_from_config and 'config'
        except AttributeError:
            pass
        # Nothing found so far! Finally just return the default value.
        return 'default'

