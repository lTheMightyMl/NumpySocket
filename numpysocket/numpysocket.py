#!/usr/bin/env python3

import asyncio
import socket
import logging
import numpy as np
from io import BytesIO


class ConfigurationError(Exception):
    """Server/Client Configuration Issue"""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'ConfigurationError, {0}'.format(self.message)
        else:
            return 'ConfigurationError raised'


class NumpySocket():
    def __init__(self):
        self.address = 0
        self.port = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reader = self.writer = None
        self.type = None  # server or client
        self.client_connection = self.client_address = None

    def start_server(self, port):
        self.type = 'server'
        self.address = ''
        self.port = port

        self.socket.bind((self.address, self.port))
        self.socket.listen(1)
        print('Waiting for a connection...')
        self.client_connection, self.client_address = self.socket.accept()
        print('Connected to: {0}'.format(self.client_address[0]))

    def end_server(self):
        self.client_connection.shutdown(1)
        self.client_connection.close()

    def receive_numpy(self):
        if self.type != 'server':
            raise ConfigurationError('Class not configured as server')

        length = None
        frame_buffer = bytearray()
        while True:
            # print(len(frame_buffer), length)
            # 65536
            # 32768
            data = self.client_connection.recv(65536)
            frame_buffer += data
            if len(frame_buffer) == length:
                break
            while True:
                if length is None:
                    if b':' not in frame_buffer:
                        break
                    # remove the length bytes from the front of frame_buffer
                    # leave any remaining bytes in the frame_buffer!
                    length_str, ignored, frame_buffer = frame_buffer.partition(b':')
                    length = int(length_str)
                if len(frame_buffer) < length:
                    break
                # split off the full message from the remaining bytes
                # leave any remaining bytes in the frame_buffer!
                frame_buffer = frame_buffer[length:]
                length = None
                break

        frame = np.load(BytesIO(frame_buffer))['frame']
        logging.debug('Frame received')
        return frame

    def receive_ack(self):
        return self.client_connection.recv(1)

    async def start_client(self, address, port):
        self.type = 'client'
        self.address = address
        self.port = port
        self.reader, self.writer = await asyncio.open_connection(self.address, self.port)

    async def send_ack(self):
        self.writer.write(b'1')
        await self.writer.drain()

    async def send_numpy(self, frame):
        if self.type != 'client':
            raise ConfigurationError('Class not configured as client')

        if not isinstance(frame, np.ndarray):
            raise TypeError('Input frame is not a valid numpy array')

        f = BytesIO()
        np.savez(f, frame=frame)

        packet_size = len(f.getvalue())
        header = '{0}:'.format(packet_size)
        header = bytes(header.encode())  # prepend length of array

        out = bytearray()
        out += header

        f.seek(0)
        out += f.read()

        try:
            self.writer.write(out)
            await self.writer.drain()
        except Exception:
            return

        logging.debug("Frame sent")
