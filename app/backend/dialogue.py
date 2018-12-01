import random
import re
from product_manger import ProductManager
from ReplyTemplet import Reply
from NLU import NLU_interface
from .policy_learning import Policy_learner

slotList = ['brand', 'memory', 'price', 'disk', 'cpu', 'gpu']
# 规定最少需要获取price、cpu和memory信息才能进行推荐
slotneeded = ['brand', 'price', 'cpu']


# slotneeded = ['cpu', 'memory', 'price']

class Dialogue:
    def __init__(self):
        self.product_manager = ProductManager()  # 相当于外部数据库的管理类，用于查询商品
        self.reply = Reply()
        # 初始化slotTable, states以及actions
        # self.slotTable = {slot_type: None for slot_type in slotList}  # 初始化
        self.slotRemain = []
        # self.states = []
        # self.actions = []
        # self.times = 0  # 用于记录用户询问的论数
        # self.flag = False  # 当进行了产品查询，并返回时，被激活，此时需要检测用户选择的第几个商品
        # self.num = 3   # 阈值，至少知道三个参数，才能推荐
        self.product_list = []
        self.slot_product_list = []
        self.game_product_list = []
        self.max_num_product = 5  # 设置产品查询的最大数量
        self.ids = None  # 用于记录选择的商品
        # 初始化NLU模型
        self.state_tracker = Policy_learner()  # 追踪当前对话状态
        # Fixme: 写死，关于review部分，会出现一次
        self.review_flag = True

    def NLU(self, request):
        """
        自然语言理解模块，将用户输入解析成slotTable
        :param request:用户的输入
        :return:
        """
        slot_table = NLU_interface.get_slot_table(request)
        return slot_table

    def Dialogue_manager(self, request):
        """
        :param request:
        :return:
        """
        # stateTracking
        new_slotTable = self.NLU(request)

        # action = self.policy_learning(new_slotTable)
        policy = self.state_tracker.learn_policy(new_slotTable, request)  # 获得action和对应的信息
        action = policy[0]
        data = policy[1]

        if action in ['init', 'end']:
            return self.NLG(action=action)
        elif action in ['slot_ask', 'slot_query']:  # slot 任务
            slot_table = data
            if action == 'slot_ask':
                _state = [i for i, j in slot_table.items() if j is not None]
                self.slotRemain = list(set(slotneeded) - set(_state))
                slot = self.slotRemain[int(random.random() * len(self.slotRemain))]
                # Fixme:关于review部分，暂时写死
                if self.review_flag == True:
                    review_label = self.get_review_label()
                    if len(review_label) != 0:
                        review_reply = self.get_review_reply()
                        return review_reply+self.NLG(action=action, slot=slot)
                return self.NLG(action=action, slot=slot)
            else:
                return self.NLG(action=action, slot_table=slot_table)
        elif action in ['game_ask', 'game_query']:  # 游戏任务
            game_list = data
            return self.NLG(action=action, game_list=game_list)
        elif action in ['buy']:
            ids = data
            return self.NLG(action=action, ids=ids)

    def NLG(self, action, **kgs):
        """
        回复生成模块：根据动作生成回复
        :param action:1. 继续询问其他配置 2. 展示数据库中查询结果 3. 确认用户需求及选择结果
        :return:
        """
        if action in ['init']:  #
            return self.reply.init()
        elif action == 'slot_ask':
            if 'slot' in kgs.keys():
                return self.reply.askValues(kgs['slot'])
            else:
                return self.reply.ask()
        elif action == 'game_ask':
            return self.reply.game_ask()
            # if 'game_list' in kgs.keys() and len(kgs['game_list']) > 0:  # 已经有一个game
        elif action == 'slot_query':
            assert 'slot_table' in kgs.keys()  # 需要查询的slot列表
            self.product_list = self.slot_search(slot_table=kgs['slot_table'])
            if len(self.product_list) == 0:  # 没有产品列表，需要告诉state_tracking
                # Fixme:这里没有检索到相应的产品怎么办
                # self.product_list = [{'name':'product test', 'price':'1234'}]  # 这里需要
                self.state_tracker.have_not_product()
            return self.reply.qry(self.product_list, action)
        elif action == 'game_query':
            assert 'game_list' in kgs.keys()  # 需要搜索的有些表
            self.product_list = self.game_search(game_list=kgs['game_list'])
            if len(self.product_list) == 0:  # 没有产品列表，需要告诉state_tracking
                # Fixme:这里没有检索到相应的产品怎么办
                # self.product_list = [{'name':'product test', 'price':'1234'}] # 这里需要
                self.state_tracker.have_not_product()
            return self.reply.qry(self.product_list, action)
        elif action == 'buy':
            assert 'ids' in kgs.keys()  # 选择商品的id
            self.ids = kgs['ids']
            return self.reply.buy(self.product_list, ids=kgs['ids'])
        elif action == 'end':
            return self.reply.end(self.product_list, ids=self.ids)

    def slot_search(self, slot_table):
        product_list = self.product_manager.get_product_list(slot_table)
        return product_list

    def game_search(self, game_list):
        product_list = self.product_manager.get_game_product_list(game_list)
        return product_list

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
                self.slotTable['price'] = (new_slot_table['price_l'] + new_slot_table['price_h']) / 2
                del new_slot_table['price_l']
                del new_slot_table['price_h']
            else:
                self.slotTable['price'] = new_slot_table['price_l']
                del new_slot_table['price_l']
        elif 'price_h' in new_slot_table:
            if 'price_l' in new_slot_table:
                self.slotTable['price'] = (new_slot_table['price_h'] + new_slot_table['price_l']) / 2
                del new_slot_table['price_l']
                del new_slot_table['price_h']
            else:
                self.slotTable['price'] = new_slot_table['price_h']
                del new_slot_table['price_l']
        self.slotTable.update(new_slot_table)  # 更新当前的slotTalbel
        current_state = [i for i, j in self.slotTable.items() if j is not None]
        self.slotRemain = list(set(slotneeded) - set(current_state))
        self.states.append(current_state)  # 将当前slot 状态记录到stats列表中
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
            ids = match[0]
            return ids
        return -1

    def get_review_reply(self):
        """
        根据用户提出用户体验的列表的回应修改，暂时在这里写死
        :return:
        """
        # Fixme:hard coding 时间来不及了
        if self.review_flag != True:
            return ''
        else:
            review_label = self.get_review_label()
            label_string = ','.join(review_label)
            result = '好的，除了'+label_string+'外，'
            self.review_flag = False
            return result

    def get_slot_table(self):
        """
        实时获得用户提出的配置要求列表
        :return:
        """
        return self.state_tracker.slotTable

    def get_review_label(self):
        """
        实时获得用户对用户体验的要求列表
        :return:
        """
        return self.state_tracker.review_label_request


if __name__ == '__main__':
    Task = Dialogue()
    request = input('Customer:')
    reply = ''
    step = 0
    while (step <= 12 or request == '好的'):
        print('Agent:' + Task.Dialogue_manager(request))
        request = input('Customer:')
