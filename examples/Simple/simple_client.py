#!/usr/bin/python3

import logging
import numpy as np
from numpysocket import NumpySocket

logger = logging.getLogger('simple client')
logger.setLevel(logging.INFO)

logger.info("waiting for frame")
npSocket = NumpySocket()

npSocket.start_server(9999)
frame = npSocket.receive_numpy()
logger.info("frame recieved")
logger.info(frame)

try:
    npSocket.endServer()
except OSError as err:
    logging.error("server already disconnected")
