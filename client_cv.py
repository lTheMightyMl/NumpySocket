# ## From https://stackoverflow.com/questions/30988033/sending-live-video-frame-over-network-in-python-opencv

import asyncio
import time
import cv2
import numpy as np
from numpysocket import NumpySocket

THREADS = 3

frames = [None] * THREADS


async def rec(ser, cli, i):
    global frames
    frames[i] = ser.receive_numpy()
    await cli.send_ack()


async def main():
    global frames

    # host_ip = '172.27.3.5'
    host_ip = 'localhost'

    receivers = []
    ack_senders = []

    for i in range(THREADS):
        tmp = NumpySocket()
        tmp.start_server(9999 - i)
        receivers.append(tmp)

    for i in range(THREADS):
        tmp = NumpySocket()
        await tmp.start_client(host_ip, 8000 + i)
        ack_senders.append(tmp)

    # Read until video is completed
    start = time.time()
    fps = 0

    while True:
        # Capture frame-by-frame
        await asyncio.gather(*[rec(receivers[i], ack_senders[i], i) for i in range(THREADS)], return_exceptions=False)
        frame = np.hstack(tuple(frames))
        cv2.imshow('Frame', frame)

        fps += 1

        # Press Q on keyboard to  exit
        if cv2.waitKey(2) & 0xFF == ord('q'):
            break
        # if keyboard.is_pressed('command'):
        #     break

    # print(fps)
    print(frame.shape)
    print(fps / (time.time() - start))

    for i in range(THREADS):
        receivers[i].end_server()
    print("Closing")


asyncio.run(main())
