import mirai.models.message
from mirai.models.message import Image
import random
doc = []


def root_proc(bot, event, msg):
    if msg == '<me':
        return bot.send(event, "您是我的主人啊！")


LOVE_MESSAGES: list
SAD_MESSAGES: list
NORM_MESSAGES: list
UNIDOLT_MESSAGES: list


def on_init():
    global LOVE_MESSAGES, SAD_MESSAGES, NORM_MESSAGES, UNIDOLT_MESSAGES

    LOVE_MESSAGES = [
        ["喜欢就好w", Image(path="emoji/emoji_smile.png")],
        ["诶嘿w", Image(path="emoji/emoji_happy.png")]
    ]

    SAD_MESSAGES = [
        ["qwq", Image(path="emoji/emoji_sad.png")],
        ["呜呜", Image(path="emoji/emoji_sad.png")],
        ["xwx", Image(path="emoji/emoji_dizzy.png")],
        ["uwu", Image(path="emoji/94652086_p0.png")]
    ]

    NORM_MESSAGES = [
        ['今天你喝牛奶了吗~', Image(path='emoji/95548472_p0.png')],
        ["仙布最可爱了", Image(path="emoji/95615307_p0.jpg")],
        ["Rua!", Image(path='emoji/93085114_p0.png')],
        ["要把快乐带给别人~", Image(path='emoji/88745054_p34.jpg')],
        ['ww', Image(path='emoji/88745054_p28.jpg')],
        ['多休息对心情好', Image(path='emoji/95110170_p0.png')],
        ['有一天世界会是本仙布的~', Image(path='emoji/96424522_p0.png')],
        ['仙布饿饿', Image(path='emoji/96399747_p0.png')],
        ['仙布要吃肉肉', Image(path='emoji/96420659_p0.png')],
        ['小妖精能有什么坏心思呢', Image(path='emoji/94876713_p0.png')],
        ['一起加油吧', Image(path='emoji/93447203_p0.png')],
        ['仙布觉得你是最棒的！', Image(path='emoji/88745054_p8.jpg')],
        ['和仙布一起变得更强大吧！', Image(path='emoji/88745054_p29.jpg')],
        ['不要失去信心！', Image(path='emoji/96420659_p0.png')],
        ['保持你的决心', Image(path='emoji/emoji_smile.png')],
        ['仙布着急睡觉']

    ]

    UNIDOLT_MESSAGES = [
        ['仙布才不笨！', Image(path='emoji/emoji_angry.png')],
        ['仙布才不笨嘛', Image(path='emoji/94652086_p0.png')],
        ['仙布哪里笨了嘛', Image(path='emoji/emoji_sad.png')]
    ]


last_choice = 0


def memoriable_choice(iter):
    global last_choice
    rnd = random.randint(0, len(iter)-2)
    if rnd >= last_choice:
        rnd += 1
    last_choice = rnd
    return iter[rnd]


def proc(bot, event, msg):
    if mirai.models.message.At(bot.qq) in event.message_chain:
        if "xwx" in msg:
            return bot.send(event, memoriable_choice(SAD_MESSAGES))
        if "不错" in msg:
            return bot.send(event, memoriable_choice(LOVE_MESSAGES))
        elif '笨蛋' in msg:
            return bot.send(event, memoriable_choice(UNIDOLT_MESSAGES))
        elif '恰' == msg:
            return bot.send(event, Image(path='emoji/ate.png'))
        else:
            return bot.send(event, memoriable_choice(NORM_MESSAGES))
