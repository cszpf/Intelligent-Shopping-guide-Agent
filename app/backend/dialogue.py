import random
import re
from product_manger import Product_maager
from ReplyTemplet import Reply
from NLU import NLU_interface


slotList = ['brand', 'memory', 'price', 'disk', 'cpu', 'gpu']
# 规定最少需要获取price、cpu和memory信息才能进行推荐
slotneeded = ['brand', 'price', 'cpu']
# slotneeded = ['cpu', 'memory', 'price']

class Dialogue:
    def __init__(self):
        self.product_manager = Product_maager()   # 相当于外部数据库的管理类，用于查询商品
        self.reply = Reply()
        # 初始化slotTable, states以及actions
        self.slotTable = {slot_type: None for slot_type in slotList}  # 初始化
        self.slotRemain = []
        self.states = []
        self.actions = []
        self.times = 0  # 用于记录用户询问的论数
        self.flag = False  # 当进行了产品查询，并返回时，被激活，此时需要检测用户选择的第几个商品
        self.num = 3   # 阈值，至少知道三个参数，才能推荐
        self.max_num_product = 5  # 设置产品查询的最大数量
        # 初始化NLU模型


    def NLU(self, request):
        """
        自然语言理解模块，将用户输入解析成slotTable
        :param request:用户的输入
        :return:
        """
        slot_table = NLU_interface.get_slot_table(request)
        if self.flag:  # 这是需要检测requeset中选择的第几个商品
            ids = self.detect_choice(request)  # ids
            if ids > 0 and ids < self.max_num_product:
                slot_table['ids'] = ids
            else:
                self.flag = False  #Fixme 如果用户没进行选择，则应该重置self.flag，以及做出一些相对的回复
        return slot_table


    def Dialogue_manager(self, request):
        """
        :param request:
        :return:
        """
        # stateTracking
        new_slotTable = self.NLU(request)
        print(new_slotTable)
        action = self.policy_learning(new_slotTable)
        print(self.slotTable)
        print(self.slotRemain)
        if action == 'ask':
            slot = self.slotRemain[int(random.random()*len(self.slotRemain))]  # 随机选择一个slot来询问
            return self.NLG(action=action, slot=slot)
        elif action == 'query':
            self.flag = True  # 标记询问
            return self.NLG(action=action)
        else:
            return self.NLG(action=action, ids = self.slotTable['ids'])

        # if 'ids' not in new_slotTable:  # Fixme:如何判断用户的意图是选择第n个商品（‘buy')
        #     self.slotTable.update(new_slotTable)
        #     _state = [i for i, j in self.slotTable.items() if j is not None]
        #     self.states.append(_state)
        #     slotRemain = set(slotneeded) - set(_state)
        #     # slot未询问成功，则重复询问
        #     if self.actions[-1].find('ask_') > -1:
        #         return self.NLG(action='ask', slot=self.actions[-1].split('_')[-1])
        #     if slotRemain:
        #         return self.NLG(action='ask', slot=list(slotRemain)[int(random.random()*len(slotRemain))])
        #     else:
        #         return self.NLG(action='ask')
        # else:
        #     if 'ids' in new_slotTable:
        #         ids = new_slotTable['ids']
        #         return self.NLG(action='buy', ids=ids)
        #     else:
        #         return self.NLG(action='query')


    def NLG(self, action, **kgs):
        """
        回复生成模块：根据动作生成回复
        :param action:1. 继续询问其他配置 2. 展示数据库中查询结果 3. 确认用户需求及选择结果
        :return:
        """
        if action == 'ask':
            if 'slot' in kgs.keys():
                self.actions.append('{}_{}'.format(action, kgs['slot']))
                print(kgs)
                return self.reply.askValues(kgs['slot'])
            else:
                self.actions.append('{}'.format(action))
                return self.reply.ask()
        elif action == 'query':
            self.actions.append('{}'.format(action))
            self.ProductList = self.search(slotTable=self.slotTable)
            return self.reply.qry(self.ProductList)
        elif action == 'buy':
            if 'ids' in kgs.keys():
                self.actions.append('{}'.format(action, kgs['ids']))
                return self.reply.buy(self.ProductList, kgs['ids'])


    def search(self, slotTable):
        productList = self.product_manager.get_product_list(slotTable)
        return productList


    def policy_learning(self, new_slot_table):
        """
        根据新的用户输入的slot tabl 以及 当前dialogue的状态：state、action等，做出决策
        :param new_slot_table:
        :return:
        """
        # 更新对话系统状态
        # new_slot_value = new_slot_table.keys()  # 新加进来的slot value
        # 处理价格问题
        if 'price_m' in new_slot_table:
            self.slotTable['price'] = new_slot_table['price_m']
            del new_slot_table['price_m']
        elif 'price_l' in new_slot_table:
            if 'price_h' in new_slot_table:
                self.slotTable['price'] = (new_slot_table['price_l'] + new_slot_table['price_h'])/2
                del new_slot_table['price_l']
                del new_slot_table['price_h']
            else:
                self.slotTable['price'] = new_slot_table['price_l']
                del new_slot_table['price_l']
        elif 'price_h' in new_slot_table:
            if 'price_l' in new_slot_table:
                self.slotTable['price'] = (new_slot_table['price_h'] + new_slot_table['price_l'])/2
                del new_slot_table['price_l']
                del new_slot_table['price_h']
            else:
                self.slotTable['price'] = new_slot_table['price_h']
                del new_slot_table['price_l']
        self.slotTable.update(new_slot_table)   # 更新当前的slotTalbel
        current_state = [i for i, j in self.slotTable.items() if j is not None]
        self.slotRemain = list(set(slotneeded) - set(current_state))
        self.states.append(current_state)       # 将当前slot 状态记录到stats列表中
        # 确定action
        if self.slotRemain:  # 如果当前state中，已有的slot值大于设定的阈值
            return 'ask'
        elif self.flag and 'ids' in current_state:  # 代表已经查询过数据库，并且用户已经做出选择
            return 'buy'
        else:
            return 'query'


    def detect_choice(self, request):
        """
        当self.flag 为True时，被执行
        :param request:
        :return:
        """
        assert self.flag
        pattern = re.compile('\d')
        match = re.search(pattern, request)
        if match:
            ids = int(match[0])
            return ids
        return -1



if __name__ == '__main__':
    Task = Diglogue()
    request = input('Customer:')
    reply = ''
    step = 0
    while(step<=12 or request == '好的'):
        print('Agent:' + Task.Dialogue_manager(request))
        request = input('Customer:')
