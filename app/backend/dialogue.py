import random
import re
from product_manger import ProductManager
from ReplyTemplet import Reply
from NLU import NLU_interface
from policy_learning import Policy_learner
import config


class Computer_Dialogue:
    def __init__(self):
        self.product_manager = ProductManager()  # 相当于外部数据库的管理类，用于查询商品
        self.reply = Reply()
        # 初始化slotTable, states以及actions
        # self.slotTable = {slot_type: None for slot_type in slotList}  # 初始化
        # self.slotRemain = list()
        self.product_list = list()  # 检索到的所有产品,每次选择一部分进行展示.
        self.product_show_part = list()  # 当前展示的produtlsit
        self.slot_product_list = list()
        self.game_product_list = list()
        self.review_product_list = list()
        # self.max_num_product = 5  # 设置产品查询的最大数量
        # self.ids = None  # 用于记录选择的商品
        # 初始化NLU模型我对cpu没要求
        self.state_tracker = Policy_learner()  # 追踪当前对话状态
        self.init_time = 0  # 用于记录用户停留在init状态的次数
        self.show_result = False  # 用来表示,是否需要展示
        # # Fixme: 写死，关于review部分，会出现一次
        # self.review_flag = True

    def nlu(self, request):
        """
        自然语言理解模块，将用户输入解析成slotTable
        :param request:用户的输入
        :return: dict
        """
        slot_table = NLU_interface.get_slot_table(request)
        return slot_table


    def get_response(self, request):
        """
        :param request:
        :return:
        """

        # stateTracking
        new_slotTable = self.nlu(request)

        # action = self.policy_learning(new_slotTable)
        self.state_tracker.learn_policy(new_slotTable, request)  # 更新state_tracker的系统状态
        # 展示
        self.state_tracker.show_system_state()
        print('=====================================\ncurrent_product_part_show:\n', self.product_show_part)
        current_state = self.state_tracker.state
        # Fixme：
        if current_state != 'query':
            self.show_result = False
        if current_state in ['init', 'end', 'exit_ask']:
            if current_state == 'init':
                self.init_time += 1
            return self.NLG(action=current_state)
        elif current_state in ['slot_ask', 'review_ask']:
            _state = [slot for slot, value in self.state_tracker.slotTable.items() if value is not None]
            none_state = [slot for slot, value in self.state_tracker.slotTable.items() if value is None]
            self.state_tracker.slotRemain = list(set(config.SLOT_NEEDED) - set(_state))
            # assert len(self.slotRemain) > 0  # Fixme 可能直接冲init过来,就可能不剩slot问
            if len(self.state_tracker.slotRemain) > 0:
                slot_ask = self.state_tracker.slotRemain[int(random.random() * len(self.state_tracker.slotRemain))]
            elif len(none_state) > 0:
                slot_ask = none_state[int(random.random()) * len(none_state)]
            else:
                print('Wrong in dialogue maneger!!!!')
            self.state_tracker.slot_current_ask = slot_ask
            if self.state_tracker.review_flag != 0:  # 有review,需要加上review的要求来问
                review_label = self.get_review_label()
                assert len(review_label) != 0
                review_reply = self.get_review_reply()
                return review_reply + self.NLG(action=current_state, slot=slot_ask)
            else:  # 只问slot
                return self.NLG(action=current_state, slot=slot_ask)
        elif current_state == 'game_ask':
            return self.reply.game_ask()
        elif current_state == 'slot_confirm':
            # Fixme:展示没写冲突
            return self.reply.slot_confirm()
        elif current_state == 'query':
            if self.state_tracker.query_change == False:  # 就是需要重新检索;如果是True的话,直接从当前的self.product_list进行检索
                self.review_product_list, self.slot_product_list, self.product_list = self.product_manager.query(
                    self.state_tracker.game_request,
                    self.state_tracker.review_request,
                    self.state_tracker.slotTable)
            # Fixme: 这里需要处理没检索到商品,需要引导用户更改条件
            # print('product_result number is:', len(self.product_list))
            self.product_choice()
            return self.NLG(action=current_state, product_list=self.product_show_part)
        elif current_state == 'change_confirm':
            slot_change = self.state_tracker.slot_change  # 需要改变的slot,一个一个问
            return self.NLG(action=current_state, slot_change=slot_change)
        elif current_state == 'buy':
            buy_choice = self.state_tracker.buy_choice
            return self.NLG(action=current_state, buy_choice=buy_choice)
        else:
            return 'Dialogue manager state Wrong in System!!!'

    def NLG(self, action, **data):
        """
        回复生成模块：根据动作生成回复
        :param action:
        :param data:
        :return:
        """
        if action == 'init':
            return self.reply.init(self.init_time)
        elif action == 'end':
            return self.reply.end()
        elif action in ['slot_ask', 'review_ask']:

            if 'slot' in data:
                return self.reply.ask_slot_values(data['slot'])
            else:
                return self.reply.ask()  # Fixme 这里有必要吗?好像没!
        elif action == 'game_ask':
            return self.reply.game_ask()
        elif action == 'slot_confirm':
            # Fixme:暂时-----------没写冲突
            return self.reply.slot_confirm()
        elif action == 'query':
            return self.reply.qry(productList=data['product_list'], action=action)
        elif action == 'change_confirm':
            return self.reply.change_confirm(slot_change=data['slot_change'])
        elif action == 'buy':
            return self.reply.buy(productList=self.product_show_part, ids=self.state_tracker.buy_choice)
        elif action == 'exit_ask':
            return self.reply.exit_ask(productList=self.product_show_part, ids=self.state_tracker.buy_choice,
                                       buy_done=self.state_tracker.buy_done)
        else:
            return 'NLG state Wrong in System!!!'

    def slot_search(self, slot_table):
        product_list = self.product_manager.get_product_list(slot_table)
        return product_list

    def game_search(self, game_list):
        product_list = self.product_manager.get_game_product_list(game_list)
        return product_list

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
        review_label = self.get_review_label()
        label_string = ','.join(review_label)
        result = '好的，除了' + label_string + '外，'
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
        return self.state_tracker.review_request

    def product_choice(self):
        """
        从self product list 中选择5个产品进行返回
        :return:
        """
        random.shuffle(self.product_list)
        sample_number = config.PRODUCT_SHOW_NUM
        self.product_show_part = list()
        self.show_result = False
        while len(self.product_list) > 0 and sample_number > 0:
            sample_number -= 1
            product = self.product_list.pop()
            # print(product)
            self.product_show_part.append(product)
        if len(self.product_show_part) > 0:
            self.show_result = True


    def get_result(self):
        """

        :return:
        """
        return self.product_show_part


    def get_review_request(self):
        """
        获取用户关于用户体验的要求
        :return:
        """
        return self.state_tracker.review_request

    def show_dialogue_state(self):
        print('=======================')
        print('dialogue state:\n')
        # print('ids         : {}'.format(self.ids))
        print('init_time   : {}'.format(self.init_time))
        print('show_result : {}'.format(self.show_result))
        print('product show: {}'.format(self.product_show_part))


    def reset_system(self):
        """
        重置系统
        :return:
        """
        # dialogue
        self.product_list = list()
        self.product_show_part = list()
        self.slot_product_list = list()
        self.game_product_list = list()
        self.review_product_list = list()
        self.init_time = 0
        self.show_result = False

        # state_tracker reset
        self.state_tracker.to_init()  # 重置系统状态
        self.state_tracker.reset()

if __name__ == '__main__':
    Task = Computer_Dialogue()
    request = input('Customer:')
    reply = ''
    step = 0
    while (step <= 12 or request == '好的'):
        print('Agent:' + Task.Dialogue_manager(request))

        request = input('Customer:')
