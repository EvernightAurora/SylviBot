from mirai import Mirai, GroupMessage, FriendMessage
from mirai.models.message import Quote, Plain
from Proc import HelpProc


doc = [
    ['回复 然后"撤回"', '撤回回复的消息']
]

helper_doc_0 = '''
撤回
用法: 回复仙布说的一句话，并且仅输入撤回
仙布布便会尽力撤回回复的那一句
请所有人监督仙布哦~
'''


def on_init():
    HelpProc.register_helper(['撤回'], helper_doc_0)


def proc(bot: Mirai, event, msg):
    msg0 = ""
    for i in event.message_chain:
        if type(i) is Plain:
            msg0 += i.text.strip()
    if msg0 == "撤回":
        # event = GroupMessage(event)
        recall_msg = None
        for i in event.message_chain:
            if type(i) is Quote:
                recall_msg = i
                break
        if not recall_msg:
            return None
        # recall_msg = Quote(recall_msg)
        if recall_msg.sender_id != bot.qq:
            return None
        recall_msg = recall_msg.id
        if type(event) is FriendMessage:
            recall_msg += 65536
        return bot.recall(recall_msg)


def root_proc(bot, event, msg):
    return None
