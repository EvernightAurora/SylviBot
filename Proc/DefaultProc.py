import mirai.models.message
from mirai.models.message import Image
import random


doc = []


comfort_key = [
    'qwq',
    '呜呜'
]

comfort_reply = [
    ['摸摸不哭~'],
    ['揉揉w'],
    [Image(path='emoji/emoji_smile.png'), '仙布会一直陪着你的~'],
    [Image(path='emoji/emoji_shock.png'), '都会好起来的~'],
    [Image(path='emoji/88745054_p8.jpg'), '强大的人才会得到别人喜爱，一起加油吧'],
    ['仙布也在无时无刻的体会着孤独，我想，孤独会让人更加强大']
]

good_night_key = [
    '晚安',
    '好梦'
]

good_night_reply = [
    ['晚安好梦~'],
    [Image(path='emoji/emoji_shock.png'), '明天是崭新的一天~'],
    [Image(path='emoji/emoji_smile.png'), '仙布一会就进入你的梦啦']
]

good_morning_key = [
    '早安',
    '早上好'
]

good_morning_reply = [
    ['早上好呀~'],
    ['昨晚的梦如何~'],
    [Image(path='emoji/emoji_smile.png'), '丝带的感觉舒服吧']
]

love_key = [
    '爱你',
    '喜欢你'
]

love_reply = [
    [Image(path='emoji/emoji_shock.png'), '仙布也爱你哟~'],
    [Image(path='emoji/88745054_p29.jpg'), '仙布最喜欢你啦']
]

thank_key = [
    '谢谢',
    '谢了'
]

thank_reply = [
    [Image(path='emoji/95110170_p0.png'), '这是应该的嘛~'],
    ['不用谢~']
]

Reply_Pair = [
    [comfort_key, comfort_reply],
    [good_night_key, good_night_reply],
    [good_morning_key, good_morning_reply],
    [love_key, love_reply],
    [thank_key, thank_reply]
]


def root_proc(bot, event, msg):
    return


def proc(bot, event, msg):
    for k, r in Reply_Pair:
        for ki in k:
            if ki in msg:
                return bot.send(event, random.choice(r))
    return bot.send(event, "伊-布-!")