from string import Template
from product_manger import Product_maager
from random import random
import json

class Reply:
    # 避免程序回复生硬死板，多准备几个模板，到时候程序随机使用
    def __init__(self):
        self._price = ['请问您的最低预算是多少？', '请问您对产品的价格有什么要求？']
        # self._price = ['请问您的想要买什么价位的呢？', '请问您对产品的价格有什么要求？']
        # self._price = ['请问您的最高预算是多少呢？', '请问您对产品的价格有什么要求？']
        self._memory = ['请问您需要多大的内存空间？', '请问您对产品的内存还有什么要求']
        self._brand = ['目前我们支持戴尔、惠普、宏碁、联想、苹果等电脑品牌，请问您倾向于购买哪种品牌机？']
        self._disk = ['请问您需要多大的硬盘容量？', '请问您对产品的硬盘容量有什么要求？']
        self._cpu = ['请问您对产品的CPU型号还有什么要求？']
        self._gpu = ['一般来说，独立显卡要比集成显卡性能好，但集成显卡要比独立显卡便宜。请问您对显卡有什么要求？']
        self._ask = Template('请问$command？')
        self._buy = Template('已为您选购一台$productName,共需支付$price')
        self._qry = Template('根据您的描述，下列产品或许满足您的需求:\n$productString')

    def askValues(self, slot='price'):
        """找到约 46
        :param slot: str, in ('price', 'memory', 'brand', 'disk', 'cpu', 'gpu'), default is 'price'
        :return:
        """
        return eval('self._{0}[int(random()*len(self._{0}))]'.format(slot))

    def ask(self):
        return self._ask.safe_substitute(command='您还有其他要求吗')

    def qry(self, productList):
        """
        :param productList dataframe
        :return:
        """
        #print(productList)
        if len(productList) == 0:
            return "不好意思，根据你的要求，在数据库中没有找到相应的产品"
        def productFormat(productList):
            reslut_string = ''
            # for i, j in enumerate(productList):
            #     string += str(i) + '. ' + str(j) + '\n'
            for index, product in productList.iterrows():
                #print(json.dumps(product))
                reslut_string += str(index+1) + ': ' + product.to_string() + '\n'
            return reslut_string

        return self._qry.safe_substitute(productString=productFormat(productList))

    def buy(self, productList, ids):
        return self._buy.safe_substitute(productName=productList.loc[ids-1,'name'], price=productList.loc[ids-1, 'price'])
