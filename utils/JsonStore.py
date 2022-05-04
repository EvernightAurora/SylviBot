import os
import json
import signal


class JsonStore:
    f_path: str
    data: any

    def read(self, default=None):
        if os.path.isfile(self.f_path):
            with open(self.f_path, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = default

    def __init__(self, fname: str, default=None):
        self.f_path = fname
        if default is None:
            default = dict()
        self.read(default)

    def flush(self):
        dir0 = os.path.split(self.f_path)[0]
        if dir0 and not os.path.isdir(dir0):
            os.makedirs(dir0)
        last = signal.getsignal(signal.SIGINT)

        def dummy(_, __):
            print('saving, do not exit qwq')
        signal.signal(signal.SIGINT, dummy)
        with open(self.f_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        signal.signal(signal.SIGINT, last)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

