import os
import json
import signal


def waiting_handler(signal, frame):
    print('file writing, wait')


class ImageData:
    data = None

    def load(self):
        if os.path.isfile(self.FName):
            with open(self.FName, 'r') as f:
                self.data = json.load(f)
            print(self.FName + '\t\t\t\tIDS load success')
        else:
            self.data = {
                "Who is Sylveon's mate?": 'me',
                "Do you love Glaceon?": "Yeah",
                "How is NaN?": "no one mention it",
                "data": dict()
            }

    def __init__(self, fname):
        self.FName = fname
        self.load()
        self.autosave = True

    def set_autosave(self, type):
        self.autosave = type

    def flush(self):
        prev = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, waiting_handler)
        dir0 = os.path.split(self.FName)[0]
        if dir0:
            if not os.path.exists(dir0):
                os.makedirs(dir0)
        with open(self.FName, 'w') as f:
            json.dump(self.data, f, indent=2)
        signal.signal(signal.SIGINT, prev)

    def has(self, lid):
        lid = str(lid)
        return lid in self.data['data'].keys()

    def add(self, lid, dat):
        self.data['data'][str(lid)] = dat
        if self.autosave:
            self.flush()

    def remove(self, id):
        self.data['data'].pop(id)
        if self.autosave:
            self.flush()

    def get(self, lid):
        lid = str(lid)
        return self.data['data'][lid]

    def get_data(self):
        return self.data['data']

    def get_flatten(self):
        ret = []
        for i in self.data['data'].keys():
            ret.append(self.data['data'][i])
        return ret
