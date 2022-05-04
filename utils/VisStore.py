import json
import os
import signal


class SeenPicture:
    def __init__(self, sfn):
        self.save_fn = sfn
        self.data = self.read()

    def read(self):
        if os.path.isfile(self.save_fn):
            print(self.save_fn + '\t\t\t\tVis load success')
            with open(self.save_fn, 'rt') as f:
                data = json.load(f)
            return data
        else:
            print('load false ' + self.save_fn)
            return {
                'count': 0,
                'who am i': 'SeenPicture v1',
                'how about Sylveon': 'cute!',
                'store': dict()
            }

    def write(self, data):
        dir0 = os.path.split(self.save_fn)[0]
        if dir0 and not os.path.exists(dir0):
            os.makedirs(dir0)
        last = signal.getsignal(signal.SIGINT)

        def dummy(_, __):
            print('saving, do not exit pwp')

        signal.signal(signal.SIGINT, dummy)
        with open(self.save_fn, 'wt') as f:
            json.dump(data, f, indent=2)
        signal.signal(signal.SIGINT, last)

    def auto_expand0(self, qid):
        if qid not in self.data['store'].keys():
            print('expanded ' + qid)
            self.data['store'][qid] = {
                'count': 0,
                'id': qid,
                'seen': dict()
            }

    def auto_expand(self, qid, imageid):
        self.auto_expand0(qid)
        if imageid not in self.data['store'][qid]['seen'].keys():
            self.data['store'][qid]['seen'][imageid] = 0

    def seen_count(self, qid, imageid):
        qid = str(qid)
        imageid = str(imageid)
        self.auto_expand(qid, imageid)
        return self.data['store'][qid]['seen'][imageid]

    def saw_again(self, qid, imageid):
        qid = str(qid)
        imageid = str(imageid)
        self.auto_expand(qid, imageid)
        self.data['store'][qid]['seen'][imageid] += 1
        self.data['store'][qid]['count'] += 1
        self.data['count'] += 1
        self.write(self.data)

    def clear_seen(self, qid):
        qid = str(qid)
        self.auto_expand0(qid)
        self.data['store'][qid]['seen'] = dict()
        self.write(self.data)

    def local_stastic(self, qid):
        qid = str(qid)
        self.auto_expand0(qid)
        ret = '共看过%d次 这个不会被清空\n' % self.data['store'][qid]['count']
        i_n = 0
        s_n = 0
        dat = self.data['store'][qid]['seen']
        for a in dat.keys():
            if dat[a] > 0:
                i_n += 1
                s_n += dat[a]
        ret += '共看过%d张图片 %d次'%(i_n, s_n)
        return ret


