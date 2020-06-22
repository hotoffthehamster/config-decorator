#######
History
#######

.. |dob| replace:: ``dob``
.. _dob: https://github.com/hotoffthehamster/dob

.. |nark| replace:: ``nark``
.. _nark: https://github.com/hotoffthehamster/nark

.. :changelog:

2.0.13 (2020-06-29)
===================

- Bugfix: Avoid typifying value (e.g., to str) before conform callback.

2.0.12 (2020-04-25)
===================

- Feature: Option to collect errors on update, rather than raise.

2.0.11 (2020-04-25)
===================

- Bugfix: ``apply_edits`` returning *mutated* default.

- Improve: Optional method to recover storable value.

2.0.10 (2020-04-18)
===================

- Bugfix: ``as_dict`` excludes custom user settings because not marked from-config.

  - That is, when a client calls ``update_gross`` to add free-form custom user
    config (i.e., settings that were not defined by an ``@section``-decorated
    config function), be sure to mark the values as from-config, and not
    from-default. Otherwise, ``as_dict`` ignores the values, thinking they're
    not from the user.

- Bugfix: When ``apply_items`` extracts config dict, ``skip_unset`` not honored.

- Feature: Option to include section even if all keys were excluded (``as_dict``).

- Feature: New classmethod for re-rooting section.

- Improve: New ``set_section`` method to add subsections.

2.0.9 (2020-04-17)
==================

- Feature: Add method to delete unused settings.

2.0.8 (2020-04-15)
==================

- Bugfix: Filter hidden items unless requested.

2.0.7 (2020-04-10)
==================

- Improve: Consistency: Raise on missing key, even when only 1 part specified.

2.0.6 (2020-04-01)
==================

- Internal: DX improvements.

2.0.5 (2020-04-01)
==================

- Internal: DX improvements.

2.0.4 (2020-03-30)
==================

- Internal: DX improvements.

2.0.3 (2020-03-30)
==================

- Internal: DX and Test improvements.

2.0.2 (2020-03-29)
==================

- Internal: DX and Test improvements.

2.0.1 (2020-03-29)
==================

- Internal: DX [Developer Experience] improvements.

2.0.0 (2020-03-29)
==================

- API change: Rename ``use_stringify`` → ``unmutated``.

- License: Release under MIT License.

- DX: Release and CI improvements.

1.0.0 (2020-01-25)
==================

- DX: Release process improvements (no new features).

0.4.0 (2020-01-19)
==================

- First official release (for |dob|_ and |nark|_).

