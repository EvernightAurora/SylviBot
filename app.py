from mirai import Mirai, FriendMessage, WebSocketAdapter, Startup, Shutdown
from mirai.models.events import GroupMessage, NudgeEvent, RequestEvent
import asyncio
from mirai.models.message import Plain

from Proc import e621Proc, GroupDefaultProc, NudgeProc, LockProc, pixivProc, DefaultProc, RecorderProc, e926Proc, \
    RecallProc, RootProc, BarProc, TransferProc, RequestProc, WikiProc, HelpProc, WordleProc

from utils import SubscribeCore, Access, ChineseOrder, configLoader
from Subscribers import GreetingSubscriberProc, PixivSubscriberProc, YoutuberSubscriberProc


def is_group_event(event):
    return type(event) is GroupMessage


def is_friend_event(event):
    return type(event) is FriendMessage


Friend_Procs = [RecallProc, RecorderProc, LockProc, RootProc, WikiProc, BarProc, NudgeProc, TransferProc,
                e621Proc, e926Proc, pixivProc, Access, RequestProc, SubscribeCore, HelpProc,
                WordleProc,
                GreetingSubscriberProc, PixivSubscriberProc, YoutuberSubscriberProc,
                DefaultProc]
Group_Procs = [RecallProc, LockProc,
               RootProc, WikiProc, BarProc, e621Proc, e926Proc, pixivProc, Access, SubscribeCore, HelpProc,
               WordleProc,
               GreetingSubscriberProc, PixivSubscriberProc, YoutuberSubscriberProc,
               GroupDefaultProc]


if __name__ == '__main__':
    bot_qq = configLoader.get_config('bot_qq', None)
    if not bot_qq:
        print('config需指定bot的qq！')
        exit()
    root_q = configLoader.get_config('root_qq', [])

    bot = Mirai(bot_qq, adapter=WebSocketAdapter(
        verify_key='yirimirai', host='localhost', port=8080
    ))


    @bot.on(FriendMessage)
    async def on_friend_message(event: FriendMessage):
        msg = ''
        for i in event.message_chain:
            if type(i) is Plain:
                msg += str(i) + ' '
        msg = msg.strip()
        msg = ChineseOrder.translate_order(msg)
        RecorderProc.record_proc(bot, event, msg)
        if msg == '<??':
            docs = []
            for s in Friend_Procs:
                if hasattr(s, 'doc'):
                    docs.extend(s.doc)
            return bot.send(event, '说明~\n' + '\n'.join([i[0] + ' - ' + i[1] for i in docs]))
        if event.sender.id in root_q:
            for n in Friend_Procs:
                if hasattr(n, 'root_proc'):
                    ret = n.root_proc(bot, event, msg)
                    if ret:
                        return ret
        for f in Friend_Procs:
            if hasattr(f, 'proc'):
                ret = f.proc(bot, event, msg)
                if ret:
                    return ret

    @bot.on(GroupMessage)
    async def on_group_message(event: GroupMessage):
        msg = ''
        for i in event.message_chain:
            if type(i) is Plain:
                msg += str(i) + ' '
        msg = msg.strip()
        msg = ChineseOrder.translate_order(msg)

        RecorderProc.record_proc(bot, event, msg)

        if event.sender.id in root_q:
            for n in Group_Procs:
                if hasattr(n, 'root_proc'):
                    ret = n.root_proc(bot, event, msg)
                    if ret:
                        return ret
        for f in Group_Procs:
            if hasattr(f, 'proc'):
                ret = f.proc(bot, event, msg)
                if ret:
                    return ret


    @bot.on(NudgeEvent)
    async def on_nudge_event(event: NudgeEvent):
        return NudgeProc.on_nudge(bot, event)


    @bot.on(RequestEvent)
    async def on_request_(event: RequestEvent):
        return RequestProc.on_requests(bot, event)


    # On init
    print(' initializing-----------------')
    Procs = Group_Procs + Friend_Procs
    Procs = list(set(Procs))
    for proc in Procs:
        if hasattr(proc, 'on_init'):
            proc.on_init()
    print(' initialized------------------')


    @bot.on(Startup)
    async def on_startup(_):
        for proc in Procs:
            if hasattr(proc, 'on_startup'):
                ret = proc.on_startup(bot)
                if asyncio.iscoroutinefunction(proc.on_startup):
                    await ret
        return None


    @bot.on(Shutdown)
    async def on_shutdown(_):
        for proc in Procs:
            if hasattr(proc, 'on_shutdown'):
                ret = proc.on_shutdown(bot)
                if asyncio.iscoroutinefunction(proc.on_shutdown):
                    await ret
        return None


    bot.run()
