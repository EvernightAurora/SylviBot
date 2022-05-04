from utils import ParseOrder
from difflib import SequenceMatcher
from mirai import Mirai
from utils import configLoader


doc = [
    ['<help (order)', '得到相关命令的帮助']
]


default_help = '''
这里是可爱的仙布~
能为你带来快乐的那种~
下面是命令大全~想得到更详细的可以<帮助 (具体命令)
*****来点图类*****
<来点清水 : 寻找p站上的清水(不r18)图
<来点康康 : 寻找p站上的图(如果不可以涩涩就等同于<来点清水)
<查询p站作者 : 尝试根据名字找p站作者，从而得到pid

以下是禁忌的命令
<来点w : 从e621上找图
<来点涩涩 : 从p站上找涩涩
*****玩游戏类*****
<来局wordle: 开始一局紧张刺激的wordle
*****不知道什么类*****
撤回 : 回复仙布的一句话然后加"撤回"从而让仙布撤回那句话
<进度条 : 显示现在正在下载的进度条

*****订阅类*****
订阅管理类:
<所有订阅 : 显示本群(人)的所有订阅
<取消订阅 : 取消某个订阅

各类订阅:
<订阅早安 : 订阅早上(不一定)的一句问候
<订阅晚安 : 订阅晚上的一句问候
<订阅p站作者 : 订阅一位来自pixiv站的作者，会将作品自动转运过来
<订阅youtube作者 : 订阅一位youtuber，会自动将新发布作品提示群内
<检测youtube作者 : 检测给定的是不是一个存在的youtuber id
*****其他活*****
仙布只能做到这些啦，更多的事找仙布的佣人吧~
牠的qq: %s
w,包括解除禁忌也是找他
'''


helpers = []   # [[keys], desc]


def register_helper(keys, desc):
    if type(keys) is str:
        keys = [keys]
    helpers.append([keys, desc])


MATCHER_INIT0 = 0.5


def find_best_matcher(spe):
    global MATCHER_INIT0
    best = MATCHER_INIT0
    index = -1
    for i in range(len(helpers)):
        for key in helpers[i][0]:
            rat = SequenceMatcher(None, key, spe).ratio()
            if rat > best:
                best = rat
                index = i
    return index


def proc(bot: Mirai, event, msg):
    result, last = ParseOrder.detect_order(msg, '<help', list(range(100)))
    if result:
        if len(last) == 0:
            return bot.send(event, default_help % str(configLoader.get_config('root_qq', [])))
        last_msg = ' '.join(last)
        ind = find_best_matcher(last_msg)
        if ind == -1:
            return bot.send(event, '没找着问的东西qwq')
        return bot.send(event, helpers[ind][1].strip())
