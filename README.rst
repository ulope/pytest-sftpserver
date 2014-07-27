=================
pytest-sftpserver
=================

.. image:: https://pypip.in/version/pytest-sftpserver/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/pytest-sftpserver/
    :alt: Latest Version
.. image:: http://img.shields.io/travis/ulope/pytest-sftpserver.svg?branch=master&style=flat
    :target: https://travis-ci.org/ulope/pytest-sftpserver
    :alt: Build status
.. image:: https://img.shields.io/coveralls/ulope/pytest-sftpserver.svg?branch=master&style=flat
    :target: https://coveralls.io/r/ulope/pytest-sftpserver?branch=master
    :alt: Code coverage
.. image:: https://pypip.in/py_versions/pytest-sftpserver/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/pytest-sftpserver/
    :alt: Supported versions
.. image:: https://pypip.in/license/pytest-sftpserver/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/pytest-sftpserver/
    :alt: License

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


TODO
====

- Add more documentation
- Add more usage examples
- Add TODOs :)


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
