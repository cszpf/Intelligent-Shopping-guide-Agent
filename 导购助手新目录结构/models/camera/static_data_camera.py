# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.dirname(__file__))
from save_and_load import load

# 必须的slot
necessaryTag = ['品牌', '级别', '画幅']
# NLU的label和中文tag之间的转换
labelToTag = {'brand': '品牌',
              'price': '价格',
              'pixel': '像素',
              'level': '级别',
              'frame': '画幅',
              'experience': '其他',
              'function': '配置要求'}
# 针对每一个slot的发问
ask_slot = {'品牌': ['请问你喜欢什么牌子呢？', '请问你需要什么牌子的呢?'],
            '价格': ['请问你预算多少？', '请问什么价位的合适呢?', '请问预期的价位是多少呢?'],
            '画幅': ['请问需要全画幅还是半画幅呢？', '相机画幅一般分为全画幅和半画幅,请问需要哪一种呢？'],
            '级别': ['请问你需要入门级,中端,还是高端的相机？', '相机可分为入门级，中端和高端,请问你需要哪一种级别的呢?']}
# informable slot的回复
listInfo = {'品牌': ['畅销的品牌有佳能、索尼呢', '比较受欢迎的牌子有佳能、索尼等'],
            '价格': ['一般常见的价位有5000左右的,1万左右的或者1万以上的呢']}

# 将中文的slot转成数据库的字段
nameToColumn = {'品牌': 'name', '价格': 'price',
                '像素': 'pixel', '画幅': 'frame', '级别': 'level', '其他': 'experience', '配置要求': 'function'}
# 可以进行调整的字段
adjustableSlot = {'价格': 'price', '像素': 'pixel', '画幅': 'frame', '级别': 'level'}
# 表示无所谓的词语
whatever_word = ['随意', '随便', '都行', '可以', '没关系']
# 确认的回复
yes_word = ['好的', '确认', '好', '嗯', '恩', '确定', '是', '是的', '可以', '行']
# 否定的回复
no_word = ['不要', '不是', '否定', '否认', '不对', '不可以', '不行', '别', '否', '不']
# 体验属性
experienceAttr = []

