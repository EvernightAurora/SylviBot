import app
from utils import JsonStore
from utils import configLoader


doc = [
    ['root: <access.add id', '设置某个群可以看怪图'],
    ['root: <access.remove id', '取消某个群可以看怪图'],
    ['<access.get', '得到哪些群可以看怪图']
]

Access = {}


Access_Json: JsonStore.JsonStore


def on_init():
    global Access_Json, Access
    def_list = configLoader.get_config('access_default_group', [])
    Access = {i: 0 for i in def_list}
    Access_Json = JsonStore.JsonStore('data/access.json', default=Access)


def root_proc(bot, event, msg):
    global Access
    msg = msg.lower()
    if msg[:len('<access.add ')] == '<access.add ':
        qid = msg[len('<access.add '):].strip()
        Access_Json.get_data()[qid] = 0
        Access_Json.flush()
        return bot.send(event, "设置成功")
    if msg[:len('<access.remove ')] == '<access.remove ':
        qid = msg[len('<access.remove '):].strip()
        if qid in Access_Json.get_data().keys():
            Access_Json.get_data().pop(qid)
            Access_Json.flush()
            return bot.send(event, "删除成功")
        else:
            return bot.send(event, "不存在")
    return None


def proc(bot, event, msg):
    global Access
    msg = msg.lower()
    if msg == '<access.get':
        return bot.send(event, "群列表: \n" + '\n'.join(list(Access_Json.get_data().keys())))
    return None


def can_access(event):
    global Access
    if not app.is_group_event(event):
        return True
    id = event.group.id
    id = str(id)
    return id in Access_Json.get_data().keys()

