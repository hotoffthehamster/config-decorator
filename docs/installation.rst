############
Installation
############

.. |virtualenv| replace:: ``virtualenv``
.. _virtualenv: https://virtualenv.pypa.io/en/latest/

.. |workon| replace:: ``workon``
.. _workon: https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html?highlight=workon#workon

To install system-wide, run as superuser::

    $ pip3 install config-decorator

To install user-local, simply run::

    $ pip3 install -U config-decorator

To install within a |virtualenv|_, try::

    $ mkvirtualenv config-decorator
    (config-decorator) $ pip install config-decorator

To develop on the project, link to the source files instead::

    (config-decorator) $ deactivate
    $ rmvirtualenv config-decorator
    $ git clone git@github.com:hotoffthehamster/config-decorator.git
    $ cd config-decorator
    $ mkvirtualenv -a $(pwd) --python=/usr/bin/python3.7 config-decorator
    (config-decorator) $ make develop

After creating the virtual environment,
to start developing from a fresh terminal, run |workon|_::

    $ workon config-decorator
    (config-decorator) $ ...

