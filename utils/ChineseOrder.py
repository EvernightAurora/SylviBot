

simplified = {
    "<帮助": "<help",

    "<订阅p站作者清水": "<subscribers.pixiv.login_safe",
    "<订阅p站作者": "<subscribers.pixiv.login_all",

    "<来点清水": "<img.pixiv.getsafe",
    "<来点涩涩": "<img.pixiv.getr18",
    "<来点来点": "<img.pixivic.get",
    "<来点康康": "<img.pixiv.get",

    "<取消订阅": "<subscribecore.logout",
    "<所有订阅": "<subscribecore.showthis",
    "<全部订阅": "<subscribecore.showthis",

    "<所有的订阅": "<subscribecore.showall",
    "<取消所有订阅": "<subscribecore.logout_from",

    "<订阅早安": "<subscribers.greeting.login_good_morning",
    "<订阅晚安": "<subscribers.greeting.login_good_night",
    "<订阅问候": "<subscribers.greeting.login_good_morning",

    "<查询p站作者": "<img.pixiv.searchuser",

    "<查询": "<wiki.search",
    "<来点w": "<img.e621.get",

    "<进度条": "<bar.query",

    "<别转发了": "<transfer.cancel",

    "<发小群去": "<transfer.to 929301688",
    "<发小群": "<transfer.next 929301688",

    "<发大群去": "<transfer.to 770114726",
    "<发大群": "<transfer.next 770114726",

    "<转发去": "<transfer.to",
    "<转发": "<transfer.next",

    "<挼大群蘑菇": "<rua 770114726 943771598",
    "<挼大群白龙": "<rua 770114726 1980983217",
    "<挼大群鼠鼠": "<rua 770114726 429236150",
    "<挼大群冰布": "<rua 770114726 1162594764",
    "<挼大群星星": "<rua 770114726 2951936427",
    "<挼大群九尾": "<rua 770114726 2097063221",

    "<挼大群": "<rua 770114726",

    "<挼小群蘑菇": "<rua 1011383394 943771598",
    "<挼小群白龙": "<rua 1011383394 1980983217",
    "<挼小群星星": "<rua 1011383394 2951936427",
    "<挼小群九尾": "<rua 1011383394 2097063221",
    "<挼小群": "<rua 1011383394",

    "<挼": "<rua",

    "<猜宝可梦计分板": '<guesspokemon.listboard',
    "<猜宝可梦记分板": '<guesspokemon.listboard',
    "<猜宝可梦积分板": '<guesspokemon.listboard',
    "<猜宝可梦": "<guesspokemon.start",
    '<重置猜宝可梦': '<guesspokemon.clearlistboard',

    '<检测伊布': '<ml.eeveenet.detect',

    '<订阅youtube作者': '<subscribers.youtube.add',
    '<检测youtube作者': '<subscribers.youtube.checkauthor',
    '<修改youtube自动解析': '<subscribers.youtube.onofflink',

    '<开始wordle': '<wordle.start',
    '<来局wordle': '<wordle.start',
    '<清空wordlecd': '<wordle.refresh',
    '<设置wordlecd': '<wordle.setcd'
}


def translate_order(msg):
    for a in simplified.keys():
        if msg[:len(a)].lower() == a.lower():
            msg = simplified[a] + msg[len(a):]
    return msg
