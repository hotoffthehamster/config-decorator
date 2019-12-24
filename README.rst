################
config-decorator
################

.. image:: https://travis-ci.com/hotoffthehamster/config-decorator.svg?branch=develop
  :target: https://travis-ci.com/hotoffthehamster/config-decorator
  :alt: Build Status

.. image:: https://codecov.io/gh/hotoffthehamster/config-decorator/branch/develop/graph/badge.svg
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
  :target: https://github.com/hotoffthehamster/config-decorator/blob/develop/LICENSE
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

Build elegant, self-documenting hierarchical user configuration
easily using object classes and ``@decorated`` class methods.

=======
Example
=======

E.g.,

.. code-block:: Python

    #!/usr/bin/env python3

    from config_decorator import section
    from config_decorator.subscriptable import Subscriptable

    def generate_config():

        @section(None)
        class ConfigRoot(object):
            '''Decorate an empty class to create the root settings section.'''
            pass


        @ConfigRoot.section('mood')
        class ConfigSection(Subscriptable):
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
        class ConfigSection(Subscriptable):
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

    cfgroot['mood']['color'] = 'blue'
    assert(cfgroot['mood']['color'] == 'blue')

    # The config object is attribute-aware.
    cfgroot.vibe.cleopatra.value = 100
    assert(cfgroot.vibe.cleopatra.value == [100])

    # The config object is environ-aware.
    import os
    from config_decorator.key_chained_val import KeyChainedValue
    KeyChainedValue._envvar_prefix = 'TEST_'
    os.environ['TEST_MOOD_VOLUME'] = '8'
    assert(cfgroot.mood.volume.value == 8)

========
Features
========

* A setting value may come from one or more sources, but the value of the
  most important source is the value used. A setting value may come from
  the following sources, ordered from most important to least:

  * A value read from command line arguments.

  * A value read from an environment variable.

  * A value read from a user-supplied dictionary (e.g., from an INI file loaded by |ConfigObj|_).

  * A default value (the return value of the decorated method used to define the setting).

* Each setting value is:

  * always type-checked, though the type check could be a no-op;

  * optionally validated, possibly against a user-supplied *choices* list;

  * always documented, either by the first decorator argument, or from the method ``'''docstring'''``;

  * sometimes hidden (e.g., for developer-only or experimental settings, to keep the user from seeing);

  * sometimes ephemeral, or not saved (e.g., for values based on other settings value that must be generated at runtime, after all value sources are loaded).

============
Keep Digging
============

* For complete usage examples, see this project's ``tests/``.

* Better yet, for a real-world usage example, see |nark|_'s ``ConfigRoot`` and related.

