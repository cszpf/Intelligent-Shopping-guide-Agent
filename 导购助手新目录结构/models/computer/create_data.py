import pandas as pd
import re
import ast
from collections import Counter
from .load_data import load_data_set
import os
import sys
#os.chdir('./app/backend')
###########################
# 全局变量
# 加载品牌列表
# Fixme: 这里最好使用一个配置文件，不用全局变量
brands_list = []
file_path = './data/computers_brands_list.txt'
module_path = os.path.dirname(__file__)    
file_path = module_path + file_path
print(os.path.abspath(file_path))
with open(file_path, encoding='utf-8') as f:
    line = f.readline().strip()
    while line:
        brands_list.append(line)
        line = f.readline().strip()

########################################
"""
    一些数据预处理函数
"""


def sub_func_1(x):
    """
    这个函数为了解决
        "品牌： 微星（MSI）" dtype: bool# 有冒号也有空格
        "品牌：微星（MSI）" # 只有冒号,没有空格
        的情况.
    (获得正确的品牌名)
    :param x:
    :return:
    """
    words = re.split(r'：| ', x)
    if len(words[1]) < 1:
        return words[2]
    else:
        return words[1]


def sub_func_2(x, tag=1):
    """
    这个函数是将brand中的，如：、戴尔(dell)、戴尔（DELL）等，拆成中文名和英文名的列表【戴尔、dell、DELL]
    :param x: 如：戴尔（dell）
    :param tag: 1: 如果同时存在中英文，返回中文；2：果同时存在中英文，返回英文；
    :return:
    """
    # 判断brand中是否有括号（分为中文括号，英文括号等）


def get_all_comput_brand():
    """
    将所有的品牌及其产品，弄成一个dataframe
    :return:
    """
    product_data = load_data_set('jingdong')

    data_1 = product_data[0]
    data_1['brand'] = data_1['attrs'].apply(lambda x: sub_func_1(x.split('\n')[0]))  #
    result = data_1[['brand', 'product_name']]
    sum = len(data_1)
    print(sum)
    for i in range(len(product_data)):
        if i == 0:
            continue
        data = product_data[i]
        print(len(data))
        sum += len(data)
        data['brand'] = data['attrs'].apply(lambda x: sub_func_1(x.split('\n')[0]))  #

        result = result.append(data[['brand', 'product_name']])
    result.to_csv('./data/brand_product_list.csv', index=False, encoding='utf-8')


def get_computer_brands_list():
    """
    获得整个电脑产品的品牌列表
    :return:
    """
    data = pd.read_csv('./data/brand_product_list.csv')
    brands_set = set(data['brand'].values)
    print(len(brands_set))
    print(brands_set)
    brands_list = []
    for brand in brands_set:
        if '（' in brand or '(' in brand:
            print(brand)
            # 存在中英两文
            brand_split = re.split(r'[（()）]', brand)
            brands_list.append(brand_split[0])  # 中文
            brands_list.append(brand_split[1])  # 英文
        else:
            # 只有一个（中文或英文）
            brands_list.append(brand)
    computer_brands = set(brands_list)
    print(len(computer_brands))
    print(computer_brands)
    file_path_save = './data/coumters_brands_list.txt'
    with open(file_path_save, 'w', encoding='utf-8') as f:
        for brand in computer_brands:
            f.write(brand)
            f.write('\n')


########################################
def mark_tag(tag, start, end, flag):
    """
    :param tag:
    :param start:
    :param end:
    :param flag:
    :return:
    """


def get_tags(data):
    """
    各种tag：品牌（brand）、处理器（processor）、内存（memory）、磁盘（disk）、显卡（GPU）
    :param data: 论坛数据，分为标题、内容、标签和文本。（内容和文本重复了）
    :return: data：与输入的data格式相同，但是tag列中，更新了相关的标签BIO
    """
    # 初始化tag，text：title + content
    # data['text'] = data.apply(lambda x: x['title'] + ' ' + x['content'], axis=1)
    data['tag'] = data['text'].apply(lambda x: ['O'] * len(x))
    # ['brand', 'memory', 'disk', 'price', 'cpu', 'gpu']
    # ['品牌', '内存', '硬盘', '价格', '处理器', '显卡']
    # 获得brand的tag
    data['tag'] = data[['tag', 'text']].apply(lambda x: get_brand(x), axis=1)

    # 获得内存
    data['tag'] = data[['tag', 'text']].apply(lambda x: get_memory(x), axis=1)

    # 获得硬盘
    data['tag'] = data[['tag', 'text']].apply(lambda x: get_disk(x), axis=1)

    # 获得价格
    data['tag'] = data[['tag', 'text']].apply(lambda x: get_price(x), axis=1)

    # 获得CPU
    data['tag'] = data[['tag', 'text']].apply(lambda x: get_cpu(x), axis=1)

    # 获得GPU
    data['tag'] = data[['tag', 'text']].apply(lambda x: get_gpu(x), axis=1)

    return data


def get_tags_single_text(data):
    """
    输入一个句子，然后slot filing的结果（BIO标注法）
    :param text: dict: {'text':text, 'tag':tag}
    :return: taglist
    """
    # get_brand
    tag_list = get_brand(data)
    data['tag'] = tag_list

    # get memory
    tag_list = get_memory(data)
    data['tag'] = tag_list

    # get disk
    tag_list = get_disk(data)
    data['tag'] = tag_list

    # get price
    tag_list = get_price(data)
    data['tag'] = tag_list

    # get CPU
    tag_list = get_cpu(data)
    data['tag'] = tag_list

    # get GPU
    tag_list = get_gpu(data)
    data['tag'] = tag_list

    return data['tag']


def get_brand(data):
    """
    获得文本中品牌的标签：brand
    :param data: ['content':xxx, 'tag':XXX]
    :return: 新的tags
    """
    text = data['text']
    tag = data['tag']

    # 判断text中是否出现任意一个品牌
    for brand in brands_list:
        brand = brand.lower()  # 变成全部小写
        text = text.lower()  # 变成全部小写
        find_index = 0  # 表示text.find 的下标
        start_index = text.find(brand, find_index)
        while start_index != -1:  # 发现到了brand
            end_index = start_index + len(brand)  # 末尾下标的下一个字符
            assert end_index - start_index > 1
            # Fixme：这里没有考虑到与tag中的其他标签0冲突的情况。
            if is_brand_chinese(brand):  # Fixme：这里没有考虑中文brand的一些情况：如“一台电脑”，"台电"是一个牌子
                if is_match_right(text, start_index, end_index, 'brand'):
                    tag[start_index] = 'B-Brand'
                    for i in range(start_index + 1, end_index):
                        tag[i] = 'I-Brand'

            else:  # 纯英文
                if start_index != 0 and end_index < len(text):
                    ch_before = text[start_index - 1]  # 前一个字符
                    ch_afer = text[end_index]  # 后一个字符
                    if ord(ch_before) in range(97, 123) or ord(ch_afer) in range(97, 123):  # 跳过这一个
                        find_index = start_index + 1
                        start_index = text.find(brand, find_index)
                        continue
                    else:  # 当前的brand是单独一个完整的英文单词
                        tag[start_index] = 'B-Brand'
                        for i in range(start_index + 1, end_index):
                            tag[i] = 'I-Brand'
            find_index = start_index + 1  # 继续寻找后文是否存在另外的brand
            start_index = text.find(brand, find_index)
            # print(brand)
    # print('output brand')
    return tag


def is_brand_chinese(brand_str):
    """
    判断一个brand是否是中文名，还是英文名。
    注意：这里的前提是，brand name中，不是中文字符就是英文字符
    :param brand_str: 品牌名
    :return:
    """
    for ch in brand_str:
        num = ord(ch)
        if num < 65 or num > 123:  # 存在非英文字符
            return True  # 只要存在一个中文，就返回
    return False


def get_memory(data):
    """
    获得文本描写内存的标签：brand
    :param data: ['content':xxx, 'tag':XXX]
    :return: 新的tags
    """
    text = data['text']
    tag = data['tag']

    pathern = re.compile('内存.{,4}\d+[Gg]|\d+[Gg].{,4}内存')  # Fixme:小数点没有考虑；范围性(2~4G)没有考虑

    all_match_iter = pathern.finditer(text)  # 返回一个迭代器

    for match in all_match_iter:
        if match == None:
            break
        # 要在匹配得到的大文本中，获取确切的词的位置
        pathern_2 = re.compile('\d+[Gg]')
        second_match = re.search(pathern_2, match.group())  # 这里不可能匹配不成功
        match_start = match.start() + second_match.start()
        match_end = match.start() + second_match.end()
        tag[match_start] = 'B-Memory'
        # tag[match_end - 1] = 'I-Meamory'
        for i in range(match_start + 1, match_end):  # 注意这里的match_end 小彪
            tag[i] = 'I-Memory'
    ## 使用re中的finditer函数来重构下面代码
    # end_index_record = 0  # 记录字符串截断的位置83+998799842+7
    # temp = text
    # while len(temp) > 0 :
    #     first_match = re.search(pathern, temp)
    #     if first_match == None: # 没有能匹配的
    #         break
    #     first_match_text = first_match.group() # 匹配得到的文本
    #     first_begin = first_match.start()
    #     first_end = first_match.end()
    #     # 要在匹配得到的大文本中，获取确切的词的位置
    #     pathern_2 = re.compile('\d+[Gg]')
    #     second_match = re.search(pathern_2, first_match_text) # 这里不可能匹配不成功
    #     match_start = end_index_record + first_begin + second_match.start()
    #     match_end = end_index_rI7ecord + first_begin + second_match.end()
    #     # Fixme:这里可以抽象成一个函数
    #     tag[match_start] = 'B-Memory'
    #     tag[match_end - 1] = 'I-Memory' # 注意这里的下标要减一
    #     for i in range(match_start + 1, match_end - 1): # 注意这里的match_end 小彪
    #         tag[i] = 'I-Memory'
    #     end_index_record += match_end  # 记录已经成功匹配的位置
    #     temp = text[end_index_record:len(text)] # 截取下一段继续寻找
    #     print(first_match_text)
    #     print(second_match.group())
    return tag


def get_disk(data):
    """
    从text中提取出关于硬盘需求的描述
    :param data: ['content':xxx, 'tag':XXX]
    :return: 新的tags
    """
    text = data['text']
    tag = data['tag']

    pathern = re.compile('硬盘.{,4}(\d{3,4}[Gg]|\d[Tt])|(\d{3,4}[Gg]|\d[Tt]).{,4}硬盘')  # Fixme:小数点没有考虑；范围性(2~4G)没有考虑

    all_match_iter = pathern.finditer(text)  # 返回一个迭代器

    for match in all_match_iter:
        if match == None:
            break
        # print(match[0])
        # 要在匹配得到的大文本中，获取确切的词的位置
        pathern_2 = re.compile('\d+[GgTt]')
        second_match = re.search(pathern_2, match.group())  # 这里不可能匹配不成功
        match_start = match.start() + second_match.start()
        match_end = match.start() + second_match.end()
        tag[match_start] = 'B-Disk'
        for i in range(match_start + 1, match_end):  # 注意这里的match_end 小彪
            tag[i] = 'I-Disk'

        # print(second_match[0])
        # end_index_record = 0  # 记录字符串截断的位置
        # temp = text
        # while len(temp) > 0 :
        # first_match = re.search(pathern, temp)
        # if first_match == None: # 没有能匹配的
        #     break
        # first_match_text = first_match.group() # 匹配得到的文本
        # first_begin = first_match.start()
        # first_end = first_match.end()
        # # 要在匹配得到的大文本get_slot_table中，获取确切的词的位置
        # pathern_2 = re.compile('\d+[GgTt]')
        # second_match = re.search(pathern_2, first_match_text) # 这里不可能匹配不成功
        # match_start = end_index_record + first_begin + second_match.start()
        # match_end = end_index_record + first_begin + second_match.end()
        # # Fixme:这里可以抽象成一个函数
        # tag[match_start] = 'B-Disk'
        # tag[match_end - 1] = 'I-Disk' # 注意这里的下标要减一
        # for i in range(match_start + 1, match_end - 1): # 注意这里的match_end 小彪
        #     tag[i] = 'I-Disk'
        # end_index_record += match_end  # 记录已经成功匹配的位置
        # temp = text[end_index_record:len(text)] # 截取下一段继续寻找
        # print(first_match_text)
        # print(second_match.group())
    return tag


def get_price(data):
    """
    从text中提取出关于电脑价格的描述
    :param data: ['content':xxx, 'tag':XXX]
    :return: 新的tags
    """
    tag = data['tag']
    n_pattern = re.compile('\d+')
    # medium price
    m_pattern = re.compile('\d{4,5}.{,1}(?=左右|上下)')
    m_match_iter = m_pattern.finditer(data['text'])
    for m_match in m_match_iter:
        start_index = m_match.start(0)
        end_index = re.search(n_pattern, data['text'][start_index:]).end(0) + start_index
        tag[start_index] = 'B-Price_m'
        for i in range(start_index + 1, end_index):  # 注意这里的match_end 小彪
            tag[i] = 'I-Price_m'
        # print(data['text'][start_index:end_index])
    # upper bound price
    u_pattern = re.compile('价.{,4}\d{4,}[^上]{,2}(?=[内下])|(?<=\d{4}[到\-~～`])\d{4,}')
    u_match_iter = u_pattern.finditer(data['text'])
    for u_match in u_match_iter:
        start_index = u_match.start(0)
        start_index = start_index + re.search(n_pattern, data['text'][start_index:]).start(0)
        end_index = re.search(n_pattern, data['text'][start_index:]).end(0) + start_index
        tag[start_index] = 'B-Price_u'
        for i in range(start_index + 1, end_index):
            tag[i] = 'I-Price_u'
        # print(data['text'][start_index:end_index])
    # lower bound price
    l_pattern = re.compile('\d{4,}(?=[到\-~～`]\d{4,})')
    l_match_iter = l_pattern.finditer(data['text'])
    for l_match in l_match_iter:
        start_index = l_match.start(0)
        end_index = l_match.end(0)
        tag[start_index] = 'B-Price_l'
        for i in range(start_index + 1, end_index):
            tag[i] = 'I-Price_l'
        # print(data['text'][start_index:end_index])
    return tag


def get_cpu(data):
    """
    提取关于CPU（处理器）的描述:
        1. 识别出i3,i5,i7 系列的pattern型号CPU：
            1）iX ：X为一个数字，表示是哪个系列的产品
            2）代：跟在1）后面，第一代往往是750/760，以后的每一代都是四位数：X---（X为2以上，表示第几代，后面三位数字表示这一代中的更新）
    :param data: ['content':xxx, 'tag':XXX]
    :return:
    """
    tag = data['tag']
    text = data['text']

    # 识别产品系列:'i5 850'pattern
    pattern = re.compile(r'i\d[ -]?(\d{3,4})?')  # Fixme:这里的 i\d 和 后面的代号数，是否统一标记. (还有，'i4 ' 空格这里需要处理下）
    match_iterator = pattern.finditer(text)
    for match in match_iterator:
        # print(match[0])
        start_index = match.start()
        end_index = match.end()
        tag[start_index] = 'B-CPU'
        for i in range(start_index + 1, end_index):  # 这里，结尾和中间，都标记为'I-CPU'，没有'E-CPU'
            tag[i] = 'I-CPU'
    return tag


def is_match_right(text, start_index, end_index, tag_type):
    """
    当使用正则项识别出符合规则的match后，有时需要根据该match前后的字符的约束，判断该match是否是合格的
    :param text: 原文本
    :param start_index: match 的开始下标
    :param end_index: match 的结束下标
    :param tag_type: 不同的tag的识别，需要设定不同类型的约束。
    :return: boolean: match合格返回true，不合格返回False
    """
    if tag_type == 'GPU':  # match的前后，不能存在英文字符或数字
        if start_index != 0:  # 保证存在上一个字符
            char = text[start_index - 1]
            char_ord = ord(char.lower())  #
            if (char_ord in range(48, 58)) or (char_ord in range(97, 123)):  # 数字和英文
                return False
        if end_index < len(text):  # 保证存在后一个字符
            char = text[end_index]
            char_ord = ord(char.lower())
            if (char_ord in range(48, 58)) or (char_ord in range(97, 123)):  # 数字和英文
                return False
    if tag_type == 'brand':
        match_text = text[start_index:end_index]
        assert is_brand_chinese(match_text)  # 这里处理中文情况
        if match_text == '台电':  # 处理台电这个牌子的特殊清空
            suffix_illegal_word = ['脑', '视']
            if end_index < len(text) and text[end_index] in suffix_illegal_word:
                return False
    return True


def get_gpu(data):
    """
    显卡：GPU、显存等，主要这两个指数
        1. 先根据GPU的三个主要生厂商：AMD，NAVIDIA和Intel 三个品牌下，不同系列的命名方式来识别
        2.
    :param data: ['content':xxx,']].appl 'tag':XXX]
    :return: 新的tags
    """
    tag = data['tag']
    text = data['text']
    # GPU型号：根据各大生厂商的系列命名来写规则
    # AMD HD系列 (基本没有，于intel的HD系列冲突，一般说HD，基本默认是因特尔系列
    # AMD R系列
    # pattern_AMD_HD = re.compile(r'(AMD)?[ ]?(HD)?[ ]?(\d[789][3579]0)', re.IGNORECASE)  # 忽略大小写
    pattern_AMD_R = re.compile(r'(AMD )?R[579][ ]?M?(\d{2}[05])X?(x\d)?',
                               re.IGNORECASE)  # Fixme:这里识别出显卡后，需要处理掉前后的空格; 识别出的match.(前后一个字符不能是英文，或数字）

    pattern_NVIDIA_GTX = re.compile(r'GTX?[ ]?\d{3,4}(TI)?M?', re.IGNORECASE)
    pattern_Intel_HD = re.compile(r'(Intel )?HD[ ]?P?\d{3,4}', re.IGNORECASE)

    pattern_list = [pattern_AMD_R, pattern_NVIDIA_GTX, pattern_Intel_HD]
    # test
    for pattern in pattern_list:
        match_iterator = pattern.finditer(text)
        for match in match_iterator:
            start_index = match.start()
            end_index = match.end()
            # 判断前后如果是数字或英文字符，则这个不算是显卡型号
            if is_match_right(text, start_index, end_index, 'GPU') == False:
                continue
            # print(match[0])
            tag[start_index] = 'B-GPU'
            for i in range(start_index + 1, end_index):
                tag[i] = 'I-GPU'
    return tag


if __name__ == '__main__':
    ############
    # 数据预处理部分
    # get_all_comput_brand()
    # get_computer_brands_list()

    ###########
    # 获得各种tag
    forum_data = pd.read_csv('./data/forum_tag.csv')
    print(forum_data.head())
    print(forum_data.isnull().any())

    result_forum = get_tags(forum_data)

    # for i, row in result_forum.iterrows():
    #     text_len = len(row['text'])
    #     tag_len = len(row['tag'])
    #     if text_len != tag_len:
    #         print('fuck')
    #         print(i)
    #         print(row)

    result_forum.to_csv('./data/forum_tag.csv', index=False, encoding='utf-8')

    ### test
    # test = 'fdf内存够大（16g）fdfd'
    # test2 = '8G 的内存就好了'
    # pathern = re.compile('内存.{,4}\d{1,2}[Gg]\W')  #
    # pathern2= re.compile('{，3}\d[Gg]\W{,3}内存')
    # pathern2 = re.compile('\d{1,2}]')
    # mat = re.search(pathern2, test2)
    # print(mat)
    # # print(mat.group(1))
    # # print(mat.group(2))
    #
    # print(mat.end())
    # print(mat.start(0))

    # Tag_list = ['Brand', 'Memory', 'Price', 'Disk', 'CPU', 'GPU']
    # Tag_list = ['B-Brand', 'I-Brand', 'E-Brand',
    #             'B-Memory', 'I-Memory', 'E-Memory',
    #             'B-Price_m', 'I-Price_m', 'E-Price_m',
    #             'B-Price_l', 'I-Price_l', 'E-Price_l',
    #             'B-Price_u', 'I-Price_u', 'E-Price_u',
    #             'B-Disk', 'I-Disk', 'E-Disk',
    #             'B-CPU', 'I-CPU', 'E-CPU',
    #             'B-GPU', 'I-GPU', 'E-GPU'
    #             ]
    # train = False
    # ckpt_path = 'forum_ckpt/'
    # config_file = 'forum_config / config_file'
    # map_file = 'forum_config/maps.pkl'
