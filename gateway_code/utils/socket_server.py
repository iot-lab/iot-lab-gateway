from __future__ import print_function

import asyncore
import collections
import logging
import multiprocessing
import socket
import threading

import serial

MAX_MESSAGE_LENGTH = 1024

LOGGER = logging.getLogger('gateway_code')


class RemoteClient(asyncore.dispatcher):

    """Wraps a remote client socket."""

    def __init__(self, host, socket, address):
        asyncore.dispatcher.__init__(self, socket)
        self.host = host
        self.outbox = collections.deque()

    def say(self, message):
        self.outbox.append(message)

    def handle_read(self):
        # when a client receive something, it sends to the other host
        client_message = self.recv(MAX_MESSAGE_LENGTH)
        self.host.broadcast_other_host(client_message, self)

    def handle_write(self):
        if not self.outbox:
            return
        message = self.outbox.popleft()
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError('Message too long')
        self.send(message)


class Host(asyncore.dispatcher):

    def __init__(self, name, linked_hosts, address):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote_clients = []
        self.address = address
        self.linked_hosts = linked_hosts

    def open(self):
        self.bind(self.address)
        self.listen(1)

    def handle_accept(self):
        socket, addr = self.accept() # For the remote client.
        LOGGER.info('Accepted client at %s', addr)
        self.remote_clients.append(RemoteClient(self, socket, addr))

    def handle_read(self):
        LOGGER.info('Received message: %s', self.read())

    def broadcast(self, message):
        LOGGER.info('Broadcasting message: %s', message)
        for remote_client in self.remote_clients:
            remote_client.say(message)

    def broadcast_other_host(self, message, sender):
        LOGGER.info('Broadcasting message to others: %s', message)
        self.linked_hosts.broadcast_other_host(message, self)


class Client(asyncore.dispatcher):

    def __init__(self, name, linked_hosts, host_address):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        LOGGER.info('Connecting to host at %s', host_address)
        self.host_address = host_address
        self.outbox = collections.deque()
        self.linked_hosts = linked_hosts

    def open(self):
        LOGGER.info('Client connect: %s', self.host_address)
        self.connect(self.host_address)
        LOGGER.info('Client connected: %s', self.host_address)

    def say(self, message):
        self.outbox.append(message)
        LOGGER.info('Enqueued message: %s', message)

    def handle_write(self):
        if not self.outbox:
            return
        message = self.outbox.popleft()
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError('Message too long')
        self.send(message)

    def handle_read(self):
        """ when receiving a message, send to the clients """
        message = self.recv(MAX_MESSAGE_LENGTH)
        LOGGER.info('Received message: %s', message)
        self.broadcast_other_host(message)

    def broadcast_other_host(self, message):
        LOGGER.info('Broadcasting message to others: %s', message)
        self.linked_hosts.broadcast_other_host(message, self)


class SocketServer(multiprocessing.Process):
    def __init__(self, node, server):
        super(SocketServer, self).__init__()
        self.daemon = True
        self.client_node = Client('Node', self, node)
        self.host_server = Host('Server', self, server)

    def broadcast_other_host(self, message, sender):
        if sender is self.client_node:
            self.host_server.broadcast(message)
        if sender is self.host_server:
            self.client_node.say(message)

    def run(self):
        self.client_node.open()
        self.host_server.open()
        asyncore.loop(timeout=1)

    def stop(self):
        self.client_node.close()
        self.host_server.close()
        self.join()
