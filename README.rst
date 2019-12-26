#######################################
config-decorator User Options Framework
#######################################
.. config-decorator Documentation

.. image:: https://travis-ci.com/hotoffthehamster/config-decorator.svg?branch=master
  :target: https://travis-ci.com/hotoffthehamster/config-decorator
  :alt: Build Status

.. image:: https://codecov.io/gh/hotoffthehamster/config-decorator/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/hotoffthehamster/config-decorator
  :alt: Coverage Status

.. image:: https://readthedocs.org/projects/config-decorator/badge/?version=latest
  :target: https://config-decorator.readthedocs.io/en/latest/
  :alt: Documentation Status

.. image:: https://img.shields.io/github/release/hotoffthehamster/config-decorator.svg?style=flat
  :target: https://github.com/hotoffthehamster/config-decorator/releases
  :alt: GitHub Release Status

.. image:: https://img.shields.io/pypi/v/config-decorator.svg
  :target: https://pypi.org/project/config-decorator/
  :alt: PyPI Release Status

.. image:: https://img.shields.io/github/license/hotoffthehamster/config-decorator.svg?style=flat
  :target: https://github.com/hotoffthehamster/config-decorator/blob/master/LICENSE
  :alt: License Status

.. |dob| replace:: ``dob``
.. _dob: https://github.com/hotoffthehamster/dob

.. |nark| replace:: ``nark``
.. _nark: https://github.com/hotoffthehamster/nark

.. |config-decorator| replace:: ``config-decorator``
.. _config-decorator: https://github.com/hotoffthehamster/config-decorator

.. |ConfigObj| replace:: ``ConfigObj``
.. _ConfigObj: https://github.com/DiffSK/configobj


User configuration framework developed for |dob|_.

========
Overview
========

``config-decorator`` makes it easy to define a hierarchical
collection of user-configurable key-value settings using
Pythonic ``@decorator`` syntax. It can be used with a modern
file round tripper, such as |ConfigObj|_, to add a capable,
robust user configuration subsystem to any application.

.. Build elegant, robust, and maintainable configuration settings
.. using common sense and ``@decorated`` class methods.

.. The configuration settings define a collection of user-settable values and
.. their defaults, as well as specifying type validation, value validation,
.. user help, and more.

.. An instantiated configuration object acts like a subscriptable ``dict``,
.. making it easy to drop into existing code.

.. The configuration settings can also be marshalled to or from a flat
.. dictionary, making it easy to persist using an external package
.. (for example, |ConfigObj|_, which reads and writes INI files to and
.. from dictionaries).

=======
Example
=======

Here's a simple example:

.. code-block:: Python

    #!/usr/bin/env python3

    from config_decorator import section

    def generate_config():

        @section(None)
        class ConfigRoot(object):
            '''Decorate an empty class to create the root settings section.'''
            pass


        @ConfigRoot.section('mood')
        class ConfigSection(object):
            '''Use the root settings section decorator to define setting groups.'''

            @property
            @ConfigRoot.setting(
                "The color",
                choices=['red', 'yellow', 'blue'],
            )
            def color(self):
                return 'red'

            @property
            @ConfigRoot.setting(
                "The volume",
                validate=lambda val: 0 <= val and val <= 11,
            )
            def volume(self):
                return 11

        @ConfigRoot.section('vibe')
        class ConfigSection(object):
            '''Another settings section.'''

            @property
            @ConfigRoot.setting(
                "Is it funky yet?",
                value_type=bool,
            )
            def funky(self):
                # Because value_type=bool, str will be converted to bool.
                # - Useful for config files where all values are strings!
                return 'False'

            @property
            @ConfigRoot.setting(
                "A list of numbers I heard in a song",
            )
            def cleopatra(self):
                return [5, 10, 15, 20, 25, 30, 35, 40]

            @property
            @ConfigRoot.setting(
                "Example showing how to use dashes in a settings name",
                name='kick-out-the-jams'
            )
            def kick_out_the_jams(self):
                return "I done kicked em out!"

        return ConfigRoot


    cfgroot = generate_config()

    # The config object is subscriptable.
    assert(cfgroot['mood']['color'] == 'red')

    # You can override defaults with user values.
    cfgroot['mood']['color'] = 'blue'
    assert(cfgroot['mood']['color'] == 'blue')

    # And you can always reset your values back to default.
    assert(cfgroot.mood.color.default == 'red')
    cfgroot.forget_config_values()
    assert(cfgroot['mood']['color'] == 'red')

    # The config object is attribute-aware (allows dot-notation).
    cfgroot.vibe.cleopatra.value = 100
    # And list-type values intelligently convert atoms to lists.
    assert(cfgroot.vibe.cleopatra.value == [100])

    # The config object is environ-aware, and prefers values it reads
    # from the environment over those from a config file.
    import os
    from config_decorator.key_chained_val import KeyChainedValue
    KeyChainedValue._envvar_prefix = 'TEST_'
    os.environ['TEST_MOOD_VOLUME'] = '8'
    assert(cfgroot.mood.volume.value == 8)

    # The config object can be flattened to a dict, which makes it easy
    # to persist settings keys and values to disk using another package.
    from configobj import ConfigObj
    saved_cfg = ConfigObj('path/to/persisted/settings')
    cfgroot.download_to_dict(saved_cfg)
    saved_cfg.write()

    # Likewise, values can be read from a dictionary, which makes loading
    # them from a file saved to disk easy to do as well.
    saved_cfg = ConfigObj('path/to/persisted/settings')
    cfgroot.update_known(saved_cfg)

========
Features
========

* A setting value may come from one or more sources, but the value of the
  most important source is the value used. A setting value may come from
  the following sources, ordered from most important to least:

  * A "forced" value set internally by the application.

  * A "cliarg" value read from command line arguments.

  * An "envvar" value read from an environment variable.

  * A "config" value read from a user-supplied dictionary
    (e.g., from an INI file loaded by |ConfigObj|_).

  * A default value (determined by decorated method used to define the setting).

* Each setting value is:

  * always type-checked, though the type check could be a no-op;

  * optionally validated, possibly against a user-supplied *choices* list;

  * always documented, either by the first decorator argument,
    or from the decorated method ``'''docstring'''``;

  * sometimes hidden (e.g., for developer-only or experimental settings,
    to keep the user from seeing the setting unless its value differs
    from the default value);

  * sometimes ephemeral, or not saved (e.g., for values based on other
    values that must be generated at runtime, after all value sources
    are loaded).

=======
Explore
=======

* For complete usage examples, see this project's ``tests/``.

* For a real-world usage example, see |nark|_'s ``ConfigRoot`` and related.

