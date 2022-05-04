

PPARSER_NORMAL = 1
PPARSER_ERROR = 2
PPARSER_OF_AUTHOR = 3
PPARSER_OF_ID = 4

last_search = []

value_compare = {
    "收藏大于": "blt",
    "blt": "blt",
    "bm": "blt",
    "收藏小于": "bgt",
    "bgt": "bgt",
    "最大页数": "max_page",
    "max_page": "max_page",
    "最多页数": "max_page",
    "页数限制": "max_page",
    "起始日期": "start_date",
    "start_date": "start_date",
    "结束日期": "end_date",
    "end_date": "end_date"
}

smode_type = [
    's_mode',
    '搜索模式'
]

smode_value = [
    's_tag',
    's_tag_full',
    's_tc'
]

author_compare = [
    '作者',
    '来自',
    'author',
    'from'
]

id_compare = [
    'id',
    '作品',
    'pid'
]

origin_compare = [
    '原图',
    'original_image'
]

DEFAULT_BLT = 400
DEFAULT_BGT = 99999
DEFAULT_PAGES = 10
DEFAULT_ID_PAGES = 20


def make_doc_():
    bgts = ','.join([i for i in value_compare.keys() if value_compare[i] == 'bgt'])
    blts = ','.join([i for i in value_compare.keys() if value_compare[i] == 'blt'])
    pages = ','.join([i for i in value_compare.keys() if value_compare[i] == 'max_page'])
    start_date = ','.join([i for i in value_compare.keys() if value_compare[i] == 'start_date'])
    end_date = ','.join([i for i in value_compare.keys() if value_compare[i] == 'end_date'])
    s_mode = ','.join(smode_type)
    authors = ','.join(author_compare)
    ids = ','.join(id_compare)
    msg = '''
搜索方法
1. p站搜索方式：  a b -c -d (e OR f OR g) 表示有ab,没有cd,efg至少满足一个的作品
1.5 p站不太支持搜索中文,哪怕tag有中文翻译。
2. 特殊搜索方式：类似于 *~:~* 的特殊筛选条件，仙布会亲自用触手来处理
    2.1 收藏(benchmark)筛选 {%s}可用于设置最小的收藏数，同理{%s}可设置最大的收藏数(有个锤子用)
        2.1.e 示例: *收藏大于:%d* *收藏小于:%d*, 同时这也是默认的设置
    2.2 页数筛选，太多页的不行。{%s}可设置筛选后的最大页数
        2.2.e 示例: *页数限制:%d* 同时这也是默认的设置
        2.2.? 关爱bot，关爱群，别乱动这个，因为真有上百页的作品
    2.3 在p站你搜索作者名不会得到想要的结果。所以{%s}可以设置作者的pid。
        2.3.e 示例: *作者:19802953*
    2.4 想得到特定ID也没有问题，{%s}可以选择特定pid作品
        2.4.e 示例: *pid:95606969*
    2.5 {%s}, {%s}可以设定起止时间，日期是8位数字年月
        2.5.e 示例 *起始日期:20220211*
    2.6 {%s}可以设置搜索模式，s_tag为默认模糊搜索, s_tag_full为严格的全字匹配， s_tc为查询标题、说明文字
        2.6.e 实例 *s_mode:s_tag_full*
3.
    有些特殊搜索方式是冲突的，例如同时指定id和author
'''%(bgts, blts, DEFAULT_BGT, DEFAULT_BLT, pages, DEFAULT_PAGES, authors, ids, start_date, end_date, s_mode)
    msg += '\n'
    return msg


def make_doc():
    bgts = ','.join([i for i in value_compare.keys() if value_compare[i] == 'bgt'])
    blts = ','.join([i for i in value_compare.keys() if value_compare[i] == 'blt'])
    pages = ','.join([i for i in value_compare.keys() if value_compare[i] == 'max_page'])
    start_date = ','.join([i for i in value_compare.keys() if value_compare[i] == 'start_date'])
    end_date = ','.join([i for i in value_compare.keys() if value_compare[i] == 'end_date'])
    s_mode = ','.join(smode_type)
    authors = ','.join(author_compare)
    ids = ','.join(id_compare)
    return '''
搜索方法
1 p站不太支持搜索中文,哪怕tag有中文翻译。
2. 特殊搜索方式：类似于 ~:~ 的特殊筛选条件，仙布会亲自用触手来处理
    2.1 收藏(benchmark)筛选 {%s}可用于设置最小的收藏数，同理{%s}可设置最大的收藏数(有个锤子用)
        2.1.e 示例: 收藏大于:%d 收藏小于:%d, 同时这也是默认的设置
    2.2 页数筛选，太多页的不行。{%s}可设置筛选后的最大页数
        2.2.e 示例: 页数限制:%d 同时这也是默认的设置
        2.2.? 关爱bot，关爱群，别乱动这个，因为真有上百页的作品
    2.3 在p站你搜索作者名不会得到想要的结果。所以{%s}可以设置作者的pid。
        2.3.1 设定作者的时候，其他筛选会被忽略，同时只能设定最多一个tag
        2.3.e 示例: 作者:19802953
    2.4 想得到特定ID也没有问题，{%s}可以选择特定pid作品
        2.4.e 示例: pid:95606969
    2.5 {%s}, {%s}可以设定起止时间，日期是8位数字年月
        2.5.e 示例 起始日期:20220211
    2.6 {%s}可以设置搜索模式，s_tag为默认模糊搜索, s_tag_full为严格的全字匹配， s_tc为查询标题、说明文字
        2.6.e 实例 s_mode:s_tag_full
3.
    有些特殊搜索方式是冲突的，例如同时指定id和author
'''%(bgts, blts, DEFAULT_BGT, DEFAULT_BLT, pages, DEFAULT_PAGES, authors, ids, start_date, end_date, s_mode)


def pixiv_parser_(search):
    normal_arg = {
        'bgt': DEFAULT_BGT,
        'blt': DEFAULT_BLT,
        'max_page': DEFAULT_PAGES,
        'last': "",
        'start_date': None,
        'end_date': None,
        's_mode': 's_tag',
        'origin': False
    }
    last = ''
    Len = len(search)
    pos = 0
    type = PPARSER_NORMAL
    while pos<Len:
        if search[pos] != '*':
            last += search[pos]
            pos += 1
            continue
        last += ' '
        end_pos = pos+1
        while end_pos<Len and search[end_pos] != '*':
            end_pos += 1
        if end_pos == Len:
            error = "*匹配失败: " + search[pos:]
            return PPARSER_ERROR, error
        raw = search[pos: end_pos+1]
        ins = raw[1:-1]
        pos = ins.find(':')
        if pos == -1:
            return PPARSER_ERROR, raw + "缺少:"
        front = ins[:pos].strip()
        back = ins[pos+1:].strip()

        #                                  normal
        if front in value_compare.keys():
            try:
                back = int(back)
                if back < 0:
                    raise ValueError
                if value_compare[front] == 'start_date' or value_compare[front] == 'end_date':
                    if len(str(back)) != 8:
                        raise ValueError
            except ValueError:
                return PPARSER_ERROR, raw + "参数不对"
            normal_arg[value_compare[front]] = back
            pos = end_pos+1
            continue

        #                                   author
        global last_search
        if front in author_compare:
            if type != PPARSER_NORMAL:
                return PPARSER_ERROR, '特殊筛选冲突'
            try:
                id = int(back)
            except ValueError:
                return PPARSER_ERROR, raw + "只能指定用户pid或之前搜索的编号数字"
            if id < 20:
                if 0 <= id < len(last_search):
                    id = last_search[id]
                else:
                    return PPARSER_ERROR, raw + '编号不存在'
            type = PPARSER_OF_AUTHOR
            normal_arg['author'] = id
            if normal_arg['blt'] == DEFAULT_BLT:
                normal_arg['blt'] = 0
            pos = end_pos+1
            continue

        #                                   id
        if front in id_compare:
            if type != PPARSER_NORMAL:
                return PPARSER_ERROR, '特殊筛选冲突'
            type = PPARSER_OF_ID
            try:
                normal_arg['id'] = int(back)
                if normal_arg['id'] < 0:
                    raise ValueError
            except ValueError:
                return PPARSER_ERROR, raw + ' id不是数字'
            if normal_arg['max_page'] == DEFAULT_PAGES:
                normal_arg['max_page'] = DEFAULT_ID_PAGES
            pos = end_pos+1
            continue

        #                                   smode
        if front in smode_type:
            if back not in smode_value:
                return PPARSER_ERROR, raw + '搜索模式不认识，应为 ' + ','.join(smode_value) + '之一'
            normal_arg['s_mode'] = back
            pos = end_pos+1
            continue

        #                                   none
        return PPARSER_ERROR, "不认识 " + raw
    normal_arg['last'] = last
    return type, normal_arg


def pixiv_parser(search):
    normal_arg = {
        'bgt': DEFAULT_BGT,
        'blt': DEFAULT_BLT,
        'max_page': DEFAULT_PAGES,
        'last': "",
        'start_date': None,
        'end_date': None,
        's_mode': 's_tag',
        'origin': False
    }
    type = PPARSER_NORMAL
    last = []
    search = search.strip()
    if search == '':
        return type, normal_arg
    searchs = search.split()
    for key in searchs:
        if ':' in key:
            pos = key.find(':')
            front = key[:pos]
            back = key[pos+1:]

            #  -------------- default ------------------
            if front in value_compare:
                try:
                    back = int(back)
                    if back < 0:
                        raise ValueError
                except ValueError:
                    return PPARSER_ERROR, key + ":后面不是数字"
                normal_arg[value_compare[front]] = back
                continue

            #  ----------------- smode ---------------
            if front in smode_type:
                if back not in smode_value:
                    return PPARSER_ERROR, key + "不合法的type"
                normal_arg['s_mode'] = back
                continue


            #  ------------------ id ------------------
            if front in id_compare:
                if type != PPARSER_NORMAL:
                    return PPARSER_ERROR, '特殊搜索冲突'
                type = PPARSER_OF_ID
                try:
                    back = int(back)
                    if back < 0:
                        raise ValueError
                except ValueError:
                    return PPARSER_ERROR, key + ' id不是有效数字'
                normal_arg['id'] = back
                if normal_arg['max_page'] == DEFAULT_PAGES:
                    normal_arg['max_page'] = DEFAULT_ID_PAGES
                continue

            # -------------------- author ---------------
            if front in author_compare:
                if type != PPARSER_NORMAL:
                    return PPARSER_ERROR, '特殊筛选冲突'
                try:
                    id = int(back)
                except ValueError:
                    return PPARSER_ERROR, key + "只能指定用户pid或之前搜索的编号数字"
                if id < 20:
                    if 0 <= id < len(last_search):
                        id = last_search[id]
                    else:
                        return PPARSER_ERROR, key + '编号不存在'
                type = PPARSER_OF_AUTHOR
                normal_arg['author'] = id
                if normal_arg['blt'] == DEFAULT_BLT:
                    normal_arg['blt'] = 0
                continue

            #  -------------------- unknown ----------------
            return PPARSER_ERROR, key + '不认识'
        elif key in origin_compare:
            normal_arg['origin'] = True
        else:
            last.append(key)
    normal_arg['last'] = ' '.join(last)
    return type, normal_arg
