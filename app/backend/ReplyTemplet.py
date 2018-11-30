from string import Template
from product_manger import ProductManager
from random import random


class Reply:
    # 避免程序回复生硬死板，多准备几个模板，到时候程序随机使用
    def __init__(self):
        self._price = ['请问您的最低预算是多少？', '请问您对电脑的价格有什么 要求？']
        # self._price = ['请问您的想要买什么价位的呢？', '请问您对产品的价格有什么要求？']
        # self._price = ['请问您的最高预算是多少呢？', '请问您对产品的价格有什么要求？']
        self._memory = ['请问您需要多大的内存空间？', '请问您对产品的内存还有什么要求']
        self._brand = ['目前我们支持戴尔、惠普、宏碁、联想、苹果等电脑品牌，请问您倾向于购买哪种品牌机？']
        self._disk = ['请问您需要多大的硬盘容量？', '请问您对产品的硬盘容量有什么要求？']
        self._cpu = ['请问您对产品的CPU型号还有什么要求？']
        self._gpu = ['一般来说，独立显卡要比集成显卡性能好，但集成显卡要比独立显卡便宜。请问您对显卡有什么要求？']

        self._init = ['您好，请问您想买台怎样的电脑？', '您好，请问有什么能帮助您？']
        self._buy = Template('请问确定购买一台价格$price的$productName吗？\n（是否确定购买，请输入“是”或“不是”)')
        self._end = Template('已为您选购一台$productName,共需支付$price。感谢您的支持!')
        self._ask = Template('请问$command？')

        self._qry = Template('根据您的描述，下列产品或许满足您的需求:\n$productString\n(请选择对应的产品编号进行购买）')
        self._game_ask = ['请问您对什么游戏有要求呢？\n（如:英雄联盟等）', '请问您平时玩什么游戏呢?']


    def askValues(self, slot='price'):
        """找到约 46
        :param slot: str, in ('price', 'memory', 'brand', 'disk', 'cpu', 'gpu'), default is 'price'
        :return:
        """
        return eval('self._{0}[int(random()*len(self._{0}))]'.format(slot))

    def ask(self):
            return self._ask.safe_substitute(command='您还有其他要求吗')

    def init(self):
        return self._init[int(random()*len(self._init))]

    def end(self, productList, ids):
        print(productList)
        print(ids)
        ids = int(ids)
        return self._end.safe_substitute(productName=productList[ids]['name'], price=productList[ids]['price'])

    def qry(self, productList, action=None):
        """
        :param productList:产品列表,形如[{'name':产品名称,'price':产品价格,'cpu':处理器,'disk':硬盘容量,'memory':内存大小},...]
        :return:
        """
        print(productList)
        if len(productList) == 0:
            if action == 'slot_query':
                return "不好意思，根据你的要求在，数据库中没有找到相应的产品。\n请更新下配置要求，以便能帮您找到对应的产品"
            elif action == 'game_query':
                return '不好意思，没能找到与当前游戏配置匹配的产品。\n请更换一款游戏。'  # Fixme：这里还有冲game_query --> slot_ask
            else:
                return "不好意思，没能找到相应的产品。\n请重新描述下您的要求。"

        def productFormat(productList):
            reslut_string = ''
            # for i, j in enumerate(productList):
            #     string += str(i) + '. ' + str(j) + '\n'
            for index, product in productList.iterrows():
                reslut_string += str(index) + ': ' + product.to_string() + '\n'
            return reslut_string
        return self._qry.safe_substitute(productString=productFormat(productList))

    def buy(self, productList, ids):
        ids = int(ids)
        # print(type(productList))
        # print(productList)
        return self._buy.safe_substitute(productName=productList.loc[ids, 'name'], price=productList.loc[ids, 'price'])

    def game_ask(self):
        return self._game_ask[int(random()*len(self._game_ask))]