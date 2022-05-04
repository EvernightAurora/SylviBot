from mirai import Mirai, FriendMessage, WebSocketAdapter
from mirai.models.events import GroupMessage
from mirai.models.message import MessageChain
import mirai.models.message


next_transfer = 0
transfer_target = 0

doc = [
    ['root: <transfer.next id', '转发下一个消息到某个群'],
    ['root: <transfer.cancel', '取消可能的发送'],
    ['root: <transfer.to id msg', '发送后面文字消息到id的群']
]


def root_proc(bot, event, msg):
    global next_transfer, transfer_target
    msg = msg.lower()
    if msg[:len("<transfer.next ")] == "<transfer.next ":

        async def local_proc():
            global transfer_target, next_transfer
            try:
                transfer_target = msg[len("<transfer.next "):]
                transfer_target = int(transfer_target.strip())
                transfer_target = await bot.get_group(transfer_target)
                next_transfer = 1
                await bot.send(event, "REC")
            except ValueError:
                next_transfer = 0
                await bot.send(event, "找不到目标群")
        return local_proc()
    if msg == '<transfer.cancel':
        next_transfer = 0
        return bot.send(event, "取消了啦")
    if msg[:len("<transfer.to ")] == "<transfer.to ":
        last = msg[len("<transfer.to "):]
        last = last.strip()
        qid = last.split()[0]
        last = last[len(qid):]
        last = last.strip()

        async def send_proc_1(last, qid):
            if last == '':
                await bot.send(event, "没消息怎么行嘛")
                return
            try:
                qid = int(qid)
            except ValueError:
                await bot.send(event, 'qid不是数字')
                return
            group = await bot.get_group(qid)
            if group is None:
                await bot.send(event, '没有这个群')
                return
            await bot.send(group, last)
        return send_proc_1(last, qid)
    if next_transfer > 0:
        next_transfer -= 1

        async def local_proc2():
            global transfer_target, next_transfer
            if next_transfer == 0:
                await bot.send(event, "REC end")
            await bot.send(transfer_target, event.message_chain)
        return local_proc2()
    return None


def proc(bot, event, msg):
    return None
