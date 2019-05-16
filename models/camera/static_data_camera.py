# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.dirname(__file__))
from save_and_load import load, read_list

# 必须的slot
necessary_tag = ['brand', 'level', 'frame', 'type', 'price']
# NLU的label和中文tag之间的转换
label_to_tag = {'brand': 'brand',
                'price': 'price',
                'pixel': 'pixel',
                'level': 'level',
                'frame': 'frame',
                'type': 'type',
                'screen': 'screen',
                'shutter': 'shutter',
                'experience': 'experience',
                'function': 'function'}
tagToLabel = {label_to_tag[k]: k for k in label_to_tag}
# 针对每一个slot的发问
ask_slot = {'brand': ['请问客官喜欢什么牌子呢？', '请问客官需要什么牌子的呢?'],
            'price': ['请问客官预算多少？', '请问什么价位的合适呢?', '请问预期的价位是多少呢?'],
            'frame': ['请问需要全画幅还是半画幅呢？', '相机画幅一般分为全画幅和半画幅,请问需要哪一种呢？'],
            'level': ['请问客官需要入门级,中端,还是高端的相机？', '相机可分为入门级,中端和高端,请问你需要哪一种级别的呢?',
                      '有入门级,中端,还有高端的相机,请问客官是需要哪种级别的相机呢?'],
            'type': ['请问客官想要什么类型的相机呢？比如微单,卡片机,单反等', '相机的类型很多（微单,单反,卡片机等）,请问客官需要哪种类型的相机呢？',
                     '相机的类型众多（微单,单反,卡片机等）,不知道客官喜欢哪一款呢？']}
# informable slot的回复
list_info = {'brand': ['畅销的品牌有佳能、索尼呢', '比较受欢迎的牌子有佳能、索尼等'],
             'price': ['一般常见的价位有5000左右的,1万左右的或者1万以上的呢',
                       '相机价格跨度很大,入门级的价位大概几千,高端相机的价位在大概一万以上哦'],
             'frame': ['画幅大致分为全画幅和半画幅,详细介绍可以参考https://zhuanlan.zhihu.com/p/36878963',
                       '客官您可以选择全画幅或者半画幅的相机哦,两者区别可以参考https://zhuanlan.zhihu.com/p/36878963'],
             'level': ['如果没有经验的用户,建议入门级哦～如果有一定了解可以选择中端或者高端的相机',
                       '如果是刚接触摄影的话,可以选择入门级的相机,当然客官有更高要求的话,可以选择中端或者高端的相机哟'],
             'type': ['相机类型丰富,详细介绍可以参考https://www.zhihu.com/question/20048256',
                      '相机类型众多,比如微单、单反,还有卡片机等等,进一步了解可以参考https://www.zhihu.com/question/20048256']}

fail_slot = {
    'brand': ['抱歉,小助手没能正确识别品牌哦,客官可以直接回复品牌名字来指定品牌',
              '哎呦,小助手没有理解清楚客官的需要的品牌,麻烦重新试一试呢'],
    'price': ['不好意思啦～小助手没能识别出有效的价格', '抱歉,小助手暂时没能理解客官的话哦,再试试？',
              '不好意思啦,小助手未能识别出您的心理价位,请重新试试吧'],
    'frame': ['真是非常抱歉,小助手没能顺利识别出画幅呢', '小助手未能识别客官您的画幅要求,可以再试试哦'],
    'level': ['真是非常抱歉,小助手没能顺利理解您想要的级别呢', '不好意思啦,小助手未能准确识别出客官对于级别的要求,您可以试试输入“入门级/中端/高端”'],
    'type': ['真是非常抱歉,小助手没能识别出类型呢'],
    'more': ['不好意思哟,这个小助手暂时理解不了哦~', '客官触及了小助手的知识盲区呢~']
}

preset = {
    'price': {'up': 10000, 'mid': 5000, 'down': 3000},
    'pixel': {'up': 4000, 'mid': 3000, 'down': 2000}
}

# 可以进行调整的字段
adjustable_slot = ['price', 'pixel', 'frame', 'level', 'type']
# 表示无所谓的词语
whatever_word = ['随意', '随便', '都行', '可以', '没关系', '不限']
# 确认的回复
yes_word = ['好的', '确认', '好', '嗯', '恩', '确定', '是', '是的', '可以', '行']
# 否定的回复
no_word = ['不要', '不是', '否定', '否认', '不对', '不可以', '不行', '别', '否', '不', '没有']

brand_list = "佳能 尼康 索尼 富士 宾得 理光 徕卡 松下" \
             "奥林巴斯 柯达 三星 哈苏 适马 卡西欧 Insta360" \
             "飞思 小米 阿尔帕 爱国者 玛米亚利图 华为 卡尔·蔡司" \
             "禄来 永诺 明基 锡恩帝 GE通用电气 米家 OPPO 柏卡 HTC" \
             "努比亚 谷歌 宝丽来 联想 Acer 宏碁 小蚁 夏普 QindredCam" \
             "萤石 CRAB Google"
brand_list = brand_list.split()
brand_list = [brand.strip() for brand in brand_list]
brand_list = [brand for brand in brand_list if brand]


def load_function(file_path):
    file = read_list(file_path)
    function_name = ['type', 'level', 'price', 'frame', 'screen', 'pixel']
    res = {}
    i = 0
    while i < len(file):
        name = file[i]
        temp = {}
        i += 1
        while i < len(file) and file[i] != '':
            line = file[i].split(':')
            for word in function_name:
                if word == line[0]:
                    temp[word] = line[1].split()
            i += 1

        res[name] = temp
        while i < len(file) and file[i] == '':
            i += 1
    return res


def load_func_synonyms(file_path):
    file = read_list(file_path)
    res = {}
    for line in file:
        line = line.split()
        std_word = line[0]
        for word in line:
            res[word] = std_word

    return res


def load_exp_synonyms(file_path):
    file = read_list(file_path)
    words = []
    for line in file:
        line = line.split()
        words.extend(line)
    return words


path = os.path.dirname(__file__)
function_attr = load_function(path + '/data/camera_func_attr.txt')
func_synonyms = load_func_synonyms(path + '/data/camera_func_synonyms.txt')

good_words = read_list(path + '/data/good_words_camera.txt')
bad_words = read_list(path + '/data/bad_words_camera.txt')

exp_synonyms = load_exp_synonyms(path + '/data/camera_synonyms.txt')
print(func_synonyms)
