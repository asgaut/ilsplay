import threading
import time
import signal
import json
import queue

from server import WebServer
import demod


keep_running = True
last_meas = {}

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        keep_running = False

def meas_func():
    return last_meas

#signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to exit')
print(json.dumps(meas_func()))
time.sleep(2)

q = queue.Queue()
s = WebServer(meas_func, q)
t = threading.Thread(target = s.serve, daemon = True)
t.start()

N = 204800
T = 1. / 2048000

while keep_running:
    try:
        if not q.empty():
            cmd = q.get()
            demod.process(cmd)
        last_meas = demod.demod(N, T)
    except queue.Empty:
        pass
    except KeyboardInterrupt:
        print("Bye")
        break

s.stop()
t.join()

