from mirai import Mirai
import traceback
import asyncio
import time
from utils import configLoader


async def send_error_async(bot: Mirai, attempt=None):
    for qq in configLoader.get_config('root_qq', []):
        await bot.send(await bot.get_friend(qq),
                       ("attempt: %d\n" % attempt if attempt is not None else "") +
                       "Error at " + time.asctime() + '\n' + traceback.format_exc())


def attempt_moving(bot: Mirai = None, max_attempt=5):

    def dummy(func):
        async def dummy2():
            attempt = 0
            while True:
                try:
                    ret = func()
                    if asyncio.iscoroutine(ret):
                        ret = await ret
                    return ret
                except:
                    attempt += 1
                    if attempt > max_attempt:
                        if bot:
                            await send_error_async(bot, attempt=attempt)
                        return None
                    await asyncio.sleep(.5)
        return dummy2
    return dummy
