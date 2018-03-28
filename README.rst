=================
pytest-sftpserver
=================

.. image:: https://img.shields.io/pypi/v/pytest-sftpserver.svg?style=flat
    :target: https://pypi.python.org/pypi/pytest-sftpserver/
    :alt: Latest Version
.. image:: http://img.shields.io/travis/ulope/pytest-sftpserver.svg?branch=master&style=flat
    :target: https://travis-ci.org/ulope/pytest-sftpserver
    :alt: Build status
.. image:: https://img.shields.io/coveralls/ulope/pytest-sftpserver.svg?branch=master&style=flat
    :target: https://coveralls.io/r/ulope/pytest-sftpserver?branch=master
    :alt: Code coverage
.. image:: https://img.shields.io/pypi/pyversions/pytest-sftpserver.svg?style=flat
    :target: https://pypi.python.org/pypi/pytest-sftpserver/
    :alt: Supported versions
.. image:: https://img.shields.io/pypi/l/pytest-sftpserver.svg?style=flat
    :target: https://pypi.python.org/pypi/pytest-sftpserver/
    :alt: License
.. image:: https://requires.io/github/ulope/pytest-sftpserver/requirements.svg?branch=master
     :target: https://requires.io/github/ulope/pytest-sftpserver/requirements/?branch=master
     :alt: Requirements Status

pytest-sftpserver is a plugin for `pytest`_ that provides a local SFTP-Server
`fixture`_.

The SFTP-Server provided by this fixture serves content not from files but
directly from Python objects.

Quickstart
==========

Assume you want to test a function that downloads a file from an SFTP-Server:

.. code-block:: python

    from contextlib import closing
    import paramiko
    def get_sftp_file(host, port, username, password, path):
        with closing(paramiko.Transport((host, port))) as transport:
            transport.connect(username=username, password=password)
            with closing(paramiko.SFTPClient.from_transport(transport)) as sftpclient:
                with sftpclient.open(path, "r") as sftp_file:
                    return sftp_file.read()

This plugin allows to test such functions without having to spin up an external
SFTP-Server by providing a pytest `fixture`_ called `sftpserver`. You use it
simply by adding a parameter named `sftpserver` to your test function:

.. code-block:: python

    def test_sftp_fetch(sftpserver):
        with sftpserver.serve_content({'a_dir': {'somefile.txt': "File content"}}):
            assert get_sftp_file(sftpserver.host, sftpserver.port, "user",
                                 "pw", "/a_dir/somefile.txt") == "File content"

As can be seen from this example `sftpserver` serves content directly from
python objects instead of files.


Installation
============

    pip install pytest-sftpserver


Supported Python versions
=========================

This package supports the following Python versions:

- 2.7, 3.4 - 3.6

TODO
====

- Add more documentation
- Add more usage examples
- Add TODOs :)


Version History
===============

1.2.0 - 2018-03-28
------------------

- Updated supported Python versions to 2.7, 3.4 - 3.6.
  Droped (official) support for 2.6 and 3.2, 3.3.
- Now always uses posixpath internally to avoid problems when running on Windows (#7, #8, thanks @dundeemt)
- Fixed broken readme badges (#14, thanks @movermeyer)


1.1.2 - 2015-06-01
------------------

- Fixed a bug in stat size calculation (#4)
- Fixed mkdir() overwriting existing content (#5)


Thanks to @zerok for both bug reports and accompanying tests.


1.1.1 - 2015-04-04
------------------

- Fixed broken `chmod()` behaviour for non-existing 'files' (Thanks @dundeemt)


1.1.0 - 2014-10-15
------------------

- Fixed broken `stat()` behaviour for non-existing 'files'
- Slightly increased test coverage


1.0.2 - 2014-07-27
------------------

- Fixed broken test on Python 2.6


1.0.1 - 2014-07-27
------------------

- Added Python 3.2 support
- Cleaned up tox configuration


1.0.0 - 2014-07-18
------------------

- Initial release


License
=======
Licensed unter the MIT License. See file `LICENSE`.


Inspiration
===========

The implementation and idea for this plugin is in part based upon:

- `pytest-localserver`_
- `sftpserver`_
- The `Twisted Conch in 60 Seconds`_ series (although I ended up not using
  twisted, this was very helpful understanding SFTP internals)


.. _pytest: http://pytest.org/latest/
.. _fixture: http://pytest.org/latest/fixture.html#fixtures-as-function-arguments
.. _pytest-localserver: https://bitbucket.org/basti/pytest-localserver
.. _sftpserver: https://github.com/rspivak/sftpserver
.. _Twisted Conch in 60 Seconds: http://as.ynchrono.us/2011/04/twisted-conch-in-60-seconds-trivial.html
