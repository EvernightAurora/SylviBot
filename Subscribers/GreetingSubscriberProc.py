from utils import SubscribeCore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from mirai import Mirai
from utils import ParseOrder, configLoader
import time
from Proc import HelpProc


greeting_scheduler: AsyncIOScheduler
Type_Name = 'Greeting_Subscriber'


# arg: [task_id :  fid + str(time.time()),
#       say_hour: str,
#       say_minute: str,
#       say_word: str]


async def on_login(bot: Mirai, fid, args):
    hour = args[1]
    minute = args[2]
    word = args[3]
    tid = args[0]
    if hour != '*':
        hour = int(hour)
    if minute != '*':
        minute = int(minute)

    @greeting_scheduler.scheduled_job('cron', hour=hour, minute=minute, id=tid, timezone='Asia/Shanghai')
    async def speak():
        await bot.send(await SubscribeCore.track_fid(bot, fid),
                       word)
        for qq in configLoader.get_config('root_qq', []):
            await bot.send(await bot.get_friend(qq), "发送了 " + word + " 到 " + fid)
    print(fid + ' 设置了问候订阅 ' + word)


async def on_logout(bot: Mirai, fid, args):
    tid = args[0]
    greeting_scheduler.remove_job(job_id=tid)
    print(fid + ' 取消了订阅 ' + args[3])


helper_doc_0 = '''
<订阅早安，<订阅晚安, <订阅问候
这三个其实是一个命令
用法: <订阅问候 hh:mm <问候语>
来设置一个订阅，让可爱仙布在指定的时间来群里说一句问候语
24h制。可以使用通配符

后两项可以忽略，忽略时，
    <订阅早安  默认是在7:30说 早上好~
    <订阅晚安  默认是在0:00说 晚安~早点睡哦

对于订阅类，可以通过<所有订阅 来查看本群(个人)的所有订阅
并通过<取消订阅 命令来取消掉
'''


def on_init():
    global greeting_scheduler
    greeting_scheduler = AsyncIOScheduler()
    global Type_Name
    SubscribeCore.register_type(type_name=Type_Name, sign_func=on_login, quit_func=on_logout,
                                description="一个定时说怪话的订阅")
    HelpProc.register_helper(['<订阅早安', '<订阅晚安', '<订阅问候'], helper_doc_0)


def is_proper_time(timestr):
    if ':' not in timestr:
        return False, None
    pos = timestr.find(':')
    front = timestr[:pos]
    back = timestr[pos+1: ]
    if front != '*':
        try:
            front = int(front)
        except ValueError:
            return False, None
    if back != '*':
        try:
            back = int(back)
        except ValueError:
            return False, None
    return True, [str(front), str(back)]


async def on_startup(bot):
    global greeting_scheduler
    greeting_scheduler.start()


async def on_shutdown(bot):
    global greeting_scheduler
    greeting_scheduler.shutdown(True)


s_g_id = 0


async def subscribe_greeting(fid, hour, minute, say):
    global s_g_id
    tid = fid + '-' + str(time.time()) + '-' + str(s_g_id)
    s_g_id += 1
    args = [tid, hour, minute, say]
    describe = '会在每天的%s:%s时说一声“%s”~' % (hour, minute, say)
    global Type_Name
    await SubscribeCore.runtime_login(target=fid, type_name=Type_Name, description=describe, args=args)


doc = [
    ['<subscribers.greeting.login_good_morning <xx:xx>, <word>', '订阅每天~说的，默认7:30说早上好~'],
    ['<subscribers.greeting.login_good_night <xx:xx>, <word>', '订阅每天~说的，默认0:0说晚安~早点睡哦~']
]


def root_proc(bot: Mirai, event, msg):
    return None


def proc(bot: Mirai, event, msg):
    result1, last1 = ParseOrder.detect_order(msg, '<subscribers.greeting.login_good_morning', list(range(100)))
    result2, last2 = ParseOrder.detect_order(msg, '<subscribers.greeting.login_good_night', list(range(100)))
    if result1 or result2:
        if result1:
            hour = '7'
            minute = '30'
            say = '早上好~'
            last = last1
        else:
            hour = '0'
            minute = '0'
            say = '晚安~早点睡哦'
            last = last2
        if len(last) > 0:
            res, pair = is_proper_time(last[0])
            if not res:
                return bot.send(event, "时间格式不正确， 应为 hh:mm 如5:30")
            hour = pair[0]
            minute = pair[1]
        if len(last) > 1:
            say = ' '.join(last[1:])

        async def _local():
            await subscribe_greeting(SubscribeCore.get_event_fid(event), hour, minute, say)
            await bot.send(event, '订阅成功~w')
        return _local()
    return None