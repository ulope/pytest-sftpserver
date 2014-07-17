# encoding: utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

try:
    from SocketServer import StreamRequestHandler, TCPServer, ThreadingMixIn
except ImportError:
    from socketserver import StreamRequestHandler, TCPServer, ThreadingMixIn
from contextlib import contextmanager
from threading import Thread, Event
from time import sleep

from paramiko.rsakey import RSAKey
from paramiko import sftp_server
from paramiko.transport import Transport

from pytest_sftpserver.consts import SERVER_KEY_PRIVATE
from pytest_sftpserver.sftp.content_provider import ContentProvider
from pytest_sftpserver.sftp.interface import VirtualSFTPServerInterface, AllowAllAuthHandler


class SFTPRequestHandler(StreamRequestHandler):
    def handle(self):
        transport = Transport(self.request)
        #transport.set_hexdump(True)
        transport.add_server_key(self.host_key)
        transport.set_subsystem_handler(
            'sftp',
            sftp_server.SFTPServer,
            VirtualSFTPServerInterface,
            content_provider=self.server.content_provider
        )

        transport.start_server(server=AllowAllAuthHandler())
        # Keep a reference to channel to avoid it getting GCed immediately
        channel = transport.accept()

        # Keep the thread alive until the client is done
        while transport.is_active():
            sleep(.5)

    @property
    def host_key(self):
        return RSAKey.from_private_key_file(SERVER_KEY_PRIVATE)


class SFTPServer(Thread, ThreadingMixIn, TCPServer):
    def __init__(self, content_object=None, content_provider_class=ContentProvider):
        self.content_provider = content_provider_class(content_object)
        TCPServer.__init__(self, ("127.0.0.1", 0), SFTPRequestHandler, False)
        Thread.__init__(self)
        self.daemon = True
        self._bound = Event()

    def run(self):
        self.server_bind()
        self.server_activate()
        self._bound.set()
        self.serve_forever()

    @contextmanager
    def serve_content(self, content_object):
        old_content_object = self.content_provider.content_object

        try:
            self.content_provider.content_object = content_object
            yield
        finally:
            self.content_provider.content_object = old_content_object

    @property
    def port(self):
        if not self.wait_for_bind():
            return None
        return self.server_address[1]

    @property
    def host(self):
        if not self.wait_for_bind():
            return None
        return self.server_address[0]

    @property
    def url(self):
        return "sftp://user:pw@{s.host}:{s.port}/".format(s=self)

    def wait_for_bind(self, timeout=.5):
        if self._bound.is_set():
            return True
        return self._bound.wait(timeout)
