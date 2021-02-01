import asyncio
import cv2
import numpy as np
from numpysocket import NumpySocket

THREADS = 3

frames = [None] * THREADS


async def send(sen, ack, i):
    global frames
    await sen.send_numpy(frames[i])
    ack.receive_ack()


async def main():
    global frames
    # host_ip = '172.27.3.3'
    # host_ip = '172.27.3.38'
    host_ip = 'localhost'

    cap = cv2.VideoCapture(0)

    senders = []
    for i in range(THREADS):
        tmp = NumpySocket()
        await tmp.start_client(host_ip, 9999 - i)
        senders.append(tmp)

    receivers = []
    for i in range(THREADS):
        tmp = NumpySocket()
        tmp.start_server(8000 + i)
        receivers.append(tmp)

    # Read until video is completed
    n_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        ref_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_resize = ref_frame[::2, ::2]
        n_frame += 1
        h, w = frame_resize.shape
        w = w // THREADS
        frames = np.array_split(frame_resize, THREADS, axis=1)
        try:
            # await asyncio.gather(*[senders[i].send_numpy(frames[i]) for i in range(THREADS)],
            #                      return_exceptions=False)
            await asyncio.gather(*[send(senders[i], receivers[i], i) for i in range(THREADS)], return_exceptions=False)
        except Exception:
            break
        for i in range(THREADS):
            receivers[i].receive_ack()

    # When everything done, release the video capture object
    for i in range(THREADS):
        receivers[i].end_server()
    cap.release()


asyncio.run(main())
