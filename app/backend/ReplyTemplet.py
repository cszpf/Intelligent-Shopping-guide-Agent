from string import Template
from product_manger import ProductManager
from random import random
import pandas as pd


class Reply:
    # 避免程序回复生硬死板，多准备几个模板，到时候程序随机使用
    def __init__(self):
        self._price = ['请问您的想要买什么价位的呢？', '请问您对电脑的价格有什么要求？']
        # self._price = ['请问您的想要买什么价位的呢？', '请问您对产品的价格有什么要求？']
        # self._price = ['请问您的最高预算是多少呢？', '请问您对产品的价格有什么要求？']
        self._memory = ['请问您需要多大的内存空间？', '请问您对产品的内存有什么要求?']
        self._brand = ['目前我们支持戴尔、惠普、宏碁、联想、苹果等电脑品牌，请问您倾向于购买哪种品牌机？']
        self._disk = ['请问您需要多大的硬盘容量？', '请问您对产品的硬盘容量有什么要求？']
        self._cpu = ['请问您对产品的CPU型号还有什么要求？\n（如：i3, i5或i7等）']
        self._gpu = ['一般来说，独立显卡要比集成显卡性能好，但集成显卡要比独立显卡便宜。请问您对显卡有什么要求？']

        self._init_1 = ['您好,请问有什么能帮助您？']
        self._init_2 = ['不好意思,我们暂时只支持电脑的导购功能.']
        self._buy = Template('请问确定购买一台价格$price的$productName吗？\n（是否确定购买，请输入“是”或“不是”)')
        self._exit_ask_1 = Template('已为您选购一台$productName,共需支付$price。感谢您的支持!\n请问您是否退出系统?(请输入"是"或"不是")')
        self._exit_ask_2 = ['请问您是否退出系统?\n(请输入"是"或"不是")']
        self._end = ['感谢您的支持,欢迎再次使用,再见!']
        self._ask = Template('请问$command？')

        # self._qry = Template('根据您的描述，下列产品或许满足您的需求:\n$productString\n(请选择对应的产品编号进行购买）')
        self._qry = ['为您推荐以下商品,可回复第几个进行选择:', '暂时没有找到符合条件的商品，换个条件试试？']
        self._game_ask = ['请问您对什么游戏有要求呢？\n（如:英雄联盟等）', '请问您平时玩什么游戏呢?']
        self._change = Template('请问是否确定将$slot_type,从$old_value更改为$new_value?\n(请回答:是/不是)')


    def ask_slot_values(self, slot='price'):
        """找到约 46
        :param slot: str, in ('price', 'memory', 'brand', 'disk', 'cpu', 'gpu'), default is 'price'
        :return:
        """
        return eval('self._{0}[int(random()*len(self._{0}))]'.format(slot))

    def ask(self):
        return self._ask.safe_substitute(command='您还有其他要求吗')

    def init(self, times):
        if times > 2:
            return self._init_2[int(random() * len(self._init_2))]
        return self._init_1[int(random() * len(self._init_1))]

    def exit_ask(self, productList, ids, buy_done):
        """
        :param productList:
        :param ids:
        :param buy_done: 标记用户是否买了商品
        :return:
        """
        if buy_done == True:
            ids = int(ids)
            return self._exit_ask_1.safe_substitute(productName=productList[ids]['name'],
                                                    price=productList[ids]['price'])
        else:
            return self._exit_ask_2[0]

    def end(self):
        return self._end[int(random() * len(self._end))]

    def qry(self, productList, action=None):
        """
        :param productList:产品列表,形如[{'name':产品名称,'price':产品价格,'cpu':处理器,'disk':硬盘容量,'memory':内存大小},...]
        :return:
        """
        # Fixme:重新设计
        # print(productList)
        # if len(productList) == 0:
        #     if action == 'slot_query':
        #         return "不好意思，根据你的要求在，数据库中没有找到相应的产品。\n请更新下配置要求，以便能帮您找到对应的产品"
        #     elif action == 'game_query':
        #         return '不好意思，没能找到与当前游戏配置匹配的产品。\n请更换一款游戏。'  # Fixme：这里还有冲game_query --> slot_ask
        #     else:
        #         return "不好意思，没能找到相应的产品。\n请重新描述下您的要求。"
        #
        # def productFormat(productList):
        #     # pd.set_option('max_colwidth', 50)
        #     reslut_string = ''
        #     # for i, j in enumerate(productList):
        #     #     string += str(i) + '. ' + str(j) + '\n'
        #     for index, product in productList.iterrows():
        #         reslut_string += str(index) + ': ' + product.to_string() + '\n'
        #     return reslut_string
        if len(productList) > 0:
            return self._qry[0]
        else:
            # Fixme: 这里需要区分:游戏\slot
            return self._qry[1]
        # return self._qry.safe_substitute(productString=productFormat(productList))

    def buy(self, productList, ids):
        ids = int(ids)
        # print(type(productList))
        # print(productList)
        print(productList)
        product_name = productList[ids-1]['name']
        if product_name is None:
            product_name = productList[ids-1]['brand'] + '电脑'
        product_price = productList[ids - 1]['price']
        return self._buy.safe_substitute(productName=product_name, price=product_price)

    def game_ask(self):
        return self._game_ask[int(random()*len(self._game_ask))]

    def slot_confirm(self):
        return 'slot_confirm'

    def change_confirm(self, slot_change):
        """
        slot的改变的确认
        :param slot_change: {'slot_name', 'new_value', 'old_value'
        :return:
        """
        # Fixme

        return self._change.safe_substitute(slot_type=slot_change['slot_name'],
                                            old_value=slot_change['old_value'],
                                            new_value=slot_change['new_value'])
