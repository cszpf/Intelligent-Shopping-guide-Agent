# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.dirname(__file__))
from save_and_load import load, read, read_list

# 品牌列表
brand_list = '''
惠普 戴尔 苹果 华硕 神舟 ThinkPad Acer 宏碁 机械革命 三星 雷神 Alienware 机械师 联想 华为 a豆 微软 小米 ROG MSI 微星 荣耀 
炫龙 LG 麦本本 雷蛇 火影 Terrans Force 海尔 技嘉 中柏 VAIO 吾空 壹号本 清华同方 东芝 锡恩帝 松下 昂达 酷比魔方 富士通 
宝扬 博本 谷歌 海鲅 索立信 ENZ 爱尔轩 紫麦 镭波 AVITA 金属大师 SOSOON 刀客 huawei razer 索尼 google 方正 台电 新蓝 gateway 
七喜 明基 长城 tcl dell mechrevo emachines 宏基 intel ibm 优派
'''
brand_list = brand_list.replace('\n', '').lower().split()

# 必须的slot
necessaryTag = ['品牌', '价格', '内存']
# NLU的label和中文tag之间的转换
labelToTag = {'brand': '品牌',
              'price': '价格',
              'memory': '内存',
              'disk': '硬盘大小',
              'cpu': '处理器',
              'gpu': '显卡',
              'experience': '体验要求',
              'function': '功能要求'}
# 针对每一个slot的发问
ask_slot = {'品牌': ['请问你喜欢什么牌子呢？', '请问你需要什么牌子的呢?'],
            '价格': ['请问你预算多少？', '请问什么价位的合适呢?', '请问预期的价位是多少呢?'],
            '内存': ['请问运行内存需要多大呢？', '请问对运行内存有什么需求吗?']}
# informable slot的回复
listInfo = {'品牌': ['畅销的品牌有惠普,戴尔,华硕呢', '比较畅销的牌子有惠普,戴尔,华硕等'],
            '价格': ['一般常见的价位有3000以下,3000-7000或者以上的呢'],
            '内存': ['常见的内存规格分为4G，6G，8G,16G等等']}

# 将中文的slot转成数据库的字段
nameToColumn = {'品牌': 'brand', '价格': 'price', '内存': 'memory', '硬盘': 'disk',
                '处理器': 'cpu', '显卡': 'gpu', '型号': 'name', '体验要求': 'experience', '功能要求': 'function'}
# 可以进行调整的字段
adjustableSlot = {'价格': 'price', '内存': 'memory', '硬盘': 'disk'}
# 表示无所谓的词语
whatever_word = ['随意', '随便', '都行', '可以', '没关系']
# 确认的回复
yes_word = ['好的', '确认', '好', '嗯', '恩', '确定', '是', '是的', '可以', '行']
# 否定的回复
no_word = ['不要', '不是', '否定', '否认', '不对', '不可以', '不行', '别', '否', '不']
# 体验属性
experienceAttr = ['信号', '做工', '分辨率', '处理器', '外观', '字体', '反应', '效果', '性价比', '性能', '手感', '拍照', '摄像', '机身', '游戏', '电池',
                  '界面',
                  '网络', '系统', '强悍', '硬件', '续航', '网速', '音质', '流畅', '视频', '软件', '重量', '音质']
# cpu　gpu等级
path = os.path.dirname(__file__)
cpu_level = load(path + '/data/cpu_level.data')
gpu_level = load(path + '/data/gpu_level.data')


def load_function(file_path):
    file = read(file_path).readlines()
    file = [line.strip() for line in file]
    function_name = ['cpu', 'gpu', 'memory']
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
                    temp[word] = line[1]
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


function_attr = load_function(path + '/data/computer_function_attr.txt')
func_synonyms = load_func_synonyms(path + '/data/computer_func_synonyms.txt')

good_words = read_list(path + '/data/good_words.txt')
bad_words = read_list(path + '/data/bad_words.txt')

exp_synonyms = load_exp_synonyms(path + '/data/computer_exp_synonyms.txt')
