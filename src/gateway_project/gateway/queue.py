import requests

from threading import Thread
from queue import Queue

storage = Queue()


class MyThread(Thread):
    def __init__(self, event):
        self.stopped = event
        super().__init__()

    def _repeat_request(self):

        if not storage.empty():
            method, url, data = storage.get()
            print(method)
            print(url)
            print(data)

            Requester.request(method, url, data)

    def run(self):
        while not self.stopped.wait(7):
            self._repeat_request()

class Requester:
    def request(method, url, data):
        if method == 'POST':
            return requests.post(url, data=data)
        elif method == 'PATCH':
            return requests.patch(url, data=data)
        elif method == 'PUT':
            return requests.put(url, data=data)
        else:
            return requests.delete(url)

# this will stop the timer
# stopFlag.set()