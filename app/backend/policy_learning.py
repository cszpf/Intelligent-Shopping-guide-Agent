import re
import random
import load_data
import pandas as pd
import config
from transitions import Machine


class State_machine():
    """
          此处为一个状态机，用于记录用户多轮对话所处的状态。注意：这里的状态，对于整个对话系统来讲，是策略
          如：query：表示需要检索产品库，获得对应的产品；如果是：ask，则需要继续询问用户相关约束条件
    """
    states = ['init', 'game_ask', 'slot_ask', 'slot_query', 'game_query', 'buy', 'end']  # 定义对话系统的状态

    def __init__(self, name='CIKE_Dialogue'):
        self.name = name
        self.machine = Machine(model=self, states=State_machine.states, initial='init')

        self.machine.add_transition('test', 'init', 'slot_ask', conditions=['transition_test'])

        # init
        self.machine.add_transition('slot_request', 'init', 'slot_ask',
                                    conditions=['is_game_match'])  # init--> slot_ask
        self.machine.add_transition('game_matcher', ['init', 'slot_ask'], 'game_ask',
                                    conditions=['is_game_match'])  # init-->game_ask 或者 slot_ask-->game_ask
        # slot_ask
        self.machine.add_transition('check_slot_ask_state', 'slot_ask', '=', conditions=['is_slot_remain'])
        self.machine.add_transition('check_slot_ask_state', 'slot_ask', 'slot_query', unless=['is_slot_remain'])
        # game_ask
        self.machine.add_transition('check_game_ask_state', 'game_ask', '=', unless=['is_get_game_name'])
        self.machine.add_transition('check_game_ask_state', 'game_ask', 'game_query', conditions=['is_get_game_name'])
        # ask_query
        self.machine.add_transition('check_ask_query', 'slot_query', 'buy', conditions=['is_customer_choice'])
        self.machine.add_transition('check_ask_query', 'slot_query', '=', unless=['is_customer_choice'])
        # game_query
        self.machine.add_transition('check_game_query', 'game_query', 'buy', conditions=['is_customer_choice'])
        self.machine.add_transition('check_game_query', 'game_query', '=', unless=['is_customer_choice'])
        # buy
        self.machine.add_transition(trigger='buy_done', source='buy', dest='end')
        # end

        # self.machine.add_transition(trigger='ask_to_query', source='ask', dest='query')
        # self.machine.add_transition(trigger='query_to_buy', source='query', dest='buy')  # 如果用户

    def transition_test(self, input):
        """
        根据输入的值，做测试
        :param input:
        :return:
        """
        if input > 10:
            return True
        return False

    '''
        就算简单的True/False问题，为啥要写成一个函数？因为改函数的策略，以后是需要改变的。
        所以，任何促发状态机状态转移的条件，都得在状态机内部定义。
    '''

    def is_slot_request(self, slot_table):
        if len(slot_table) == 0:
            return False
        return True

    def is_game_match(self, game_request):
        if len(game_request) == 0:
            return False
        return True

    def is_slot_remain(self, slot_remain):
        if len(slot_remain) == 0:
            return False
        return True

    def is_get_game_name(self, game_list):
        if len(game_list) == 0:
            return False
        return True

    def is_customer_choice(self, ids):
        if ids == -1 and ids > 5:  # 最多显示5个
            return False
        return True

class Policy_learner():
    """
        这个policy learner，其实包含了state tracker，因为在这里记录整个对话过程中slot状态和采用的行为
    """
    states = ['init', 'chat', 'slot_ask', 'review_ask', 'game_ask', 'slot_confirm', 'query', 'change_confirm', 'buy',
              'exit_ask', 'end']

    # transitions = [  # 如果有闲聊模块，这里的目的state是chat
    #     {'trigger': 'init_state', 'source': 'init', 'dest': 'init', 'conditions': 'init_to_chat'},
    #
    #     {'trigger': 'init_state', 'source': 'init', 'dest': 'slot_ask',
    #      'conditions': 'init_to_slotAsk'},
    #     {'trigger': 'init_state', 'source': 'init', 'dest': 'review_ask',
    #      'conditions': 'init_to_reviewAsk'},
    #     {'trigger': 'init_state', 'source': 'init', 'dest': 'game_ask', 'conditions': 'init_to_gameAsk'},
    #
    #     # {'trigger': 'chat_state', 'source': 'init', 'dest': 'chat', 'conditions': 'chat_to_init'},
    #     # {'trigger': 'slot_remain_state', 'source': 'slot_remain', 'dest': 'slot_ask',
    #     #  'conditions': 'slotRemain_to_slotAsk'},
    #     # {'trigger': 'slot_remain_state', 'source': 'slot_remain', 'dest': 'query',
    #     #  'conditions': 'slotRemain_to_query'},
    #
    #     {'trigger': 'slot_ask_state', 'source': 'slot_ask', 'dest': 'review_ask',
    #      'conditions': 'slotAsk_to_reviewAsk'},
    #     {'trigger': 'slot_ask_state', 'source': 'slot_ask', 'dest': 'slot_remain',
    #      'conditions': 'slotAsk_to_slotRemain'},
    #     {'trigger': 'slot_ask_state', 'source': 'slot_ask', 'dest': 'query',
    #      'conditions': 'slotAsk_to_query'},
    #     {'trigger': 'slot_ask_state', 'source': 'slot_ask', 'dest': 'game_ask',
    #      'conditions': 'slotAsk_to_gameAsk'},
    #
    #     {'trigger': 'review_ask_state', 'source': 'review_ask', 'dest': 'slot_remain',
    #      'conditions': 'reviewAsk_to_slotRemain'},
    #
    #     {'trigger': 'game_ask_state', 'source': 'game_ask', 'dest': 'query',
    #      'conditions': 'gameAsk_to_query'},
    #     {'trigger': 'game_ask_state', 'source': 'game_ask', 'dest': 'slot_confirm',
    #      'conditions': 'gameAsk_to_slotComfirm'},
    #
    #     {'trigger': 'slot_confirm_state', 'source': 'slot_confirm', 'dest': 'query',
    #      'conditions': 'slotComfirm_to_query'},
    #
    #     {'trigger': 'query_state', 'source': 'query', 'dest': 'query', 'conditions': 'query_to_query'},
    #     {'trigger': 'query_state', 'source': 'query', 'dest': 'slot_change',
    #      'conditions': 'query_to_slot_change'},
    #     {'trigger': 'query_state', 'source': 'query', 'dest': 'buy', 'conditions': 'query_to_buy'},
    #
    #     {'trigger': 'slot_change_state', 'source': 'slot_change', 'dest': 'change_confirm',
    #      'conditions': 'slotChange_to_changeConfirm'},
    #
    #     {'trigger': 'change_confirm_state', 'source': 'change_confirm', 'dest': 'query',
    #      'conditions': 'changeConfirm_to_query'},
    #
    #     {'trigger': 'buy_state', 'source': 'buy', 'dest': 'buy_confirm', 'conditions': 'buy_to_buyConfirm'},
    #
    #     {'trigger': 'buy_confirm_state', 'source': 'buy_confirm', 'dest': 'exit_ask',
    #      'conditions': 'buyConfirm_to_exitAsk'},
    #
    #     {'trigger': 'exit_ask_state', 'source': 'exit_ask', 'dest': 'init', 'conditions': 'exitAsk_to_init'},
    #     {'trigger': 'exit_ask_state', 'source': 'exit_ask', 'dest': 'end', 'conditions': 'exitAsk_to_end'}
    #
    # ]  # 可能不用这样

    def __init__(self):
        #######################################
        # Fixme: 加载数据，可以考虑配置文件
        self.all_game_list = load_data.load_text_file('./data/game_list.txt')
        self.review_label_list = pd.read_csv('./data/label_productId.csv', encoding='utf-8')['label'].tolist()

        #######################################
        # 用于记录系统状态的各种变量
        self.slotTable = {slot_type: None for slot_type in config.SLOT_LIST}  # 初始化slot table
        self.slotRemain = []
        self.slot_current_ask = None  # 用来记录当前询问的slot
        self.history_states = []
        self.history_actions = []

        self.computer_flag = False  # 用于记录，用户的意图是不是买电脑

        self.game_flag = 0  # 0:没提到；1：没提到具体游戏；2：提到了具体的游戏（也就是：game_request 不为空）
        self.game_request = list()

        self.review_flag = 0  # 0:没提到；1：没提到具体用于体验要求；2：提到了具体的要求（也就是：game_request 不为空）
        self.review_request = list()  # 用于记录用户提到的体验要求

        self.exit_flag = False  # 用于判断是否要退出系统

        self.comfirm_flag = None  # 如果需要再次确认的，使用这个来记录
        self.query_first = False  # 用户不再提需求，直接要查询
        self.query_change = False  # 用户在产品列表中，提出需要换一批
        self.slot_change_list = list()  # list of dict：用于记录用户修改的slot。多个
        self.slot_change = dict  # 一次confirm确定一个
        self.buy_done = False  # 标记用户是否购买
        self.buy_choice = -1  # 用于记录用户选择了哪个产品
        #########################################
        # 状态机
        self.state_tracker = Machine(model=self, states=Policy_learner.states, initial='init')  # 当前系统的状态追踪

    ###########################################
    def learn_policy(self, nlu_slots, request):
        """
        学习整个当前对话系统应该采用的行为
        :param nlu_slots: 从NLU中识别处关于slotTable中的值
        :param request: 由于当前NLU只能识别处那几种值，但系统还需要用到根据当前状态做的一些识别：
            1）ids：给出产品列表后，用户选择的编号
            2）game：用户提出购买能玩相关游戏的模糊搜索需要识别的类型
            3) buy_or_not: 用户选定相应产品时，询问用户是否确定购买
            4）
        :return:
        """
        ########################################
        # 识别request中需要的变量
        self.get_game_request(request=request)  # 游戏 + 更新
        self.get_review_request(request=request)  # 用户体验 + 更新
        self.get_exit_flag(request=request)  # 退出

        ########################################
        # 根据当前slot_current_ask, 来修正一下nlu中可能没有识别出来的slot值
        if self.state in ['slot_ask', 'review_ask']:
            self.fix_nlu_slot_miss(nlu_slots, request)
            self.detect_slot_ask_answer(nlu_slots, request)
        else:
            print('没有进入识别特殊情况slot的函数')
        ########################################
        # 更新slotTable:除了query状态(需要改slot的值)
        if self.state != 'query':
            self.update_slot_Table(nlu_slots)  # 在其中识别出修改的slot

        ########################################
        # 调用当前状态的触发器
        current_state_func = self.state + '_state_transition'
        getattr(self, current_state_func)(nlu_slots, request)  # 调用当前状态的策略函数

        ########################################

    def define_policy_return(self):
        """
        根据不同的状态机的状态，返回不同的数据。
        init : state, None
        slot_ask : (state, slotTable)
        game_ask : (state, game_list)
        slot_query : (state, slotTable)
        game_query : (state, game_list)
        buy : (state, ids)
        :param state: 当前系统状态
        :param **data: 用于传入一些特殊的，需要返回的值
        :return:
        """
        state = self.state  # 当前的state
        data_return = {}
        if state in ['init', 'end']:
            return state, data_return
        elif state == 'slot_ask':
            _state = [slot for slot, value in self.slotTable.items() if value is not None]
            self.slotRemain = list(set(config.SLOT_NEEDED) - set(_state))
            self.slot_current_ask = self.slotRemain[int(random.random() * len(self.slotRemain))]
            data_return['slot_type'] = self.slot_current_ask
            return state, data_return
        elif state == 'review_ask':
            _state = [slot for slot, value in self.slotTable.items() if value is not None]
            self.slotRemain = list(set(config.SLOT_NEEDED) - set(_state))
            if len(self.slotRemain) != 0:
                self.slot_current_ask = self.slotRemain[int(random.random() * len(self.slotRemain))]
                data_return['slot_ask'] = self.slot_current_ask
            data_return['reviews'] = self.review_request()
            return state, data_return
        elif state == 'game_ask':
            return state
        # elif state == 'slot_confirm':
        # elif state == 'query':
        # elif state == 'change_confirm':
        # elif state == 'buy':
        # elif state == 'exit_ask':
        # elif state == 'end':
        #
        # elif state in ['slot_ask', 'slot_query']:
        #     return state, self.slotTable
        # elif state in ['game_ask', 'game_query']:
        #     return state, self.game_list
        # elif state in ['buy']:
        #
        #     if 'ids' in data.keys():
        #
        #         return state, data['ids']
        #     else:
        #         print('输入数据有问题')
        #         return None
        #         exit(-1)

    ###########################################
    # 一系列抽取函数
    def get_game_request(self, request):
        """
        获得关于游戏的信息：
            1. 更新game_flag
            2. 如果有提到相关游戏，记录在game_requst
        :param request: 用户句子
        """
        current_game = list()  # 用于记录当前request提到的游戏
        for game in self.all_game_list:
            game = game.lower()
            request = request.lower()
            start_index = request.find(game, 0)
            if start_index != -1:
                current_game.append(game)
        self.update_game_list(current_game)  # 更新用户列表
        if len(self.game_request) > 0:
            self.game_flag = 2
        else:
            game_rule = re.compile('玩游戏')
            match = re.search(game_rule, request)
            if match is not None:
                start_index = match.start()
                if start_index == 0 or request[start_index - 1] not in ['不', '少']:
                    self.game_flag = 1

    def get_review_request(self, request):
        """
        :param request:
        :return:
        """
        # Fixme 这里暂时直接匹配
        current_label = list()
        for label in self.review_label_list:
            label = label.lower()
            request = request.lower()
            start_index = request.find(label, 0)
            if start_index != -1:
                current_label.append(label)  # 找到一个label要求
        self.update_review_label_request(current_label)
        if len(current_label) > 0:
            self.review_flag = 2
        else:
            self.review_flag = 0
        # Fixme:什么情况才是：”没有提具体的关于体验的任何要求，但又需要问的情况？

    def get_exit_flag(self, request):
        """
        规则：识别用户向退出系统的意图
        :param request:
        :return:
        """
        # Fixme: 规则
        exit_word = ['不买', '不要']
        if self.state != 'query':
            for word in exit_word:  # 在query中，表示换一批。
                if word in request.lower():
                    self.exit_flag = True

    def is_review_tag(selff, request):
        """
        判断用户的句子，有没有给出关于电脑的一些标签。
        如：【简单方便，轻薄精巧，小巧轻便】等
        :param request:
        :return:
        """

    ###########################################
    # 一系列系统状态更新函数
    def reset(self):
        """
        用户重置用户需求：将原有slottable充值为None
        :return:
        """
        self.slotTable = {slot_type: None for slot_type in config.SLOT_LIST}  # 初始化slot table
        self.slotRemain = list()
        self.slot_current_ask = None  # 用来记录当前询问的slot
        self.computer_flag = False  # 用于记录，用户的意图是不是买电脑
        self.game_flag = 0  # 0:没提到；1：没提到具体游戏；2：提到了具体的游戏（也就是：game_request 不为空）
        self.game_request = list()

        self.review_flag = 0  # 0:没提到；1：没提到具体用于体验要求；2：提到了具体的要求（也就是：game_request 不为空）
        self.review_request = list()  # 用于记录用户提到的体验要求

        self.exit_flag = False  # 用于判断是否要退出系统
        self.comfirm_flag = None  # 如果需要再次确认的，使用这个来记录
        self.query_first = False  # 用户不再提需求，直接要查询
        self.query_change = False  # 用户在产品列表中，提出需要换一批
        self.slot_change_list = list()  # list of dict：用于记录用户修改的slot。多个
        self.slot_change = dict  # 一次confirm确定一个
        self.buy_done = False  # 标记用户是否购买
        self.buy_choice = -1

    def update_slot_Table(self, new_slot_table):
        """
        更新当前系统的slot_Table
        :param new_slot_table:
        :return:
        """
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
        self.slotRemain = list(set(config.SLOT_NEEDED) - set(current_state))

    def update_game_list(self, game_request):
        """
        更新当前用户对游戏的要求列表
        :param game_request: list
        :return:
        """
        self.game_request = list(set(self.game_request) | set(game_request))

    def update_review_label_request(self, review_label):
        self.review_request = list(set(self.review_request) | set(review_label))

    ###########################################
    # 一些其他的特殊情况的处理函数
    def detect_indent(self, request):
        """
        判断用户是不是想买电脑
        :param request:
        :return:
        """
        if '电脑' in request.lower() or '笔记本' in request.lower():
            self.computer_flag = True

    def detect_choice(self, request):
        """
        当self.flag 为True时，被执行
        :param request:
        :return: 选择的数字
        """
        assert self.state == 'query'
        pattern = re.compile('\d')
        match = re.search(pattern, request)
        if match:
            ids = match[0]
            return int(ids)
        return -1

    def detect_buy_choice(self, request):
        """
        判断用户是否购买商品
        :param request:
        :return:
        """
        if '不是' in request.lower():
            return 0
        elif '是' in request.lower():
            return 1
        else:  # Fixme 不确定
            return 0

    def detect_exit_chocie(self, request):
        """
        判断用户是否选择退出
        :param request:
        :return:
        """
        if '不是' in request.lower():
            return 0
        elif '是' in request.lower():
            return 1
        else:  # Fixme 不确定
            return 0

    def have_not_product(self):
        """
        没有检索到产品，需要改变系统状态吗？策略如何？
        :return:
        """
        current_state = self.state  # 当前状态

        if current_state == 'slot_query':  # 重新问下配置
            self.to_slot_ask()
            # Fixme
        elif current_state == 'game_query':
            # print()
            self.to_game_ask()  # 换游戏？
            # fixme
        else:
            print('系统状态出错')
            exit(-1)

    def show_system_state(self):
        """
        用于展示当前系统的状态。
        :return:
        """
        print('=====================================')
        print('Policy learner state:')
        print('state        :  {}'.format(self.state))
        print('slot tatble  :  {}'.format(self.slotTable))
        print('slot remain  :  {}'.format(self.slotRemain))
        print('slot ask now :  {}'.format(self.slot_current_ask))
        print('computer flag:  {}'.format(self.computer_flag))
        print('game flag    :  {}'.format(self.game_flag))
        print('game request :\n{}'.format(self.game_request))
        print('review flag  :  {}'.format(self.review_flag))
        print('review list  :\n{}'.format(self.review_request))
        print('exit flag    :  {}'.format(self.exit_flag))
        print('comfirm flag :  {}'.format(self.comfirm_flag))
        print('query first  :  {}'.format(self.query_first))
        print('query_change :  {}'.format(self.query_change))
        print('buy_choice :  {}'.format(self.buy_choice))
        print('buy_done :  {}'.format(self.buy_done))


    def detect_change_product_list(self, request):
        """
        检测用户想换一批的想法
        :param request:
        :return:
        """
        # Fixme
        # pattern = re.compile('[看|换].{,2}[(别的)|(其他的)]')
        pattern = re.compile('(换|看|有没有).{,2}(一批|别的|其他)')
        match = re.search(pattern, request)
        if match != None:
            return True
        return False

    def detect_game_ask_conflict(self, nlu_slots, request):
        """
        检测到，游戏的最低配置，与给定的slot有冲突。
        :param nlu_slots:
        :param request:
        :return:
        """
        # Fixme: 暂时先直接使用游戏的配置进行选择
        return False

    def detect_slot_change(self, nlu_slots, request):
        """
        检测用户是否修改slot。
        这里的Nlu slots 是当前request的提取出来的，所以，与当前系统slotTable是不一样的。后面才更新这些值
        :param nlu_slots:
        :param request:
        :return: list of dict: [{'slot_name':XXX, 'new':XXX, 'old':XXX]
        """
        result = list()
        if len(nlu_slots) == 0:  # 没有提新的slot
            return result
        for slot in nlu_slots.keys():  # 遍历当前的识别到的所有slot
            slot_name = slot
            if slot_name in ['price_m', 'price_u', 'price_l']:
                slot_name = 'price'
            new_value = nlu_slots[slot]
            old_value = self.slotTable[slot_name]
            change = {'slot_name': slot_name, 'new_value': new_value, 'old_value': old_value}
            result.append(change)
        return result

    def detect_query_first(self, request):
        assert self.state == 'slot_ask'
        # Fixme
        # 假如用户说，都行怎么办
        return False

    def detect_slot_ask(self, request):

        """
        检测用户:
        :param request:
        :return:
        """

    def fix_nlu_slot_miss(self, nlu_slots, request):
        """
        :param nlu_slots: 这里可能没识别到
        :param request:
        :return:
        """
        print('go in to the slot miss Fix')
        print('nlu_slots is :', nlu_slots)
        print('request is :', nlu_slots)
        if self.slot_current_ask == 'memory':
            memory_pattern = re.compile('\d+[Gg]')
            match = re.match(memory_pattern, request)
            if match is not None and self.slot_current_ask not in nlu_slots:
                nlu_slots[self.slot_current_ask] = match[0]
                self.slotTable[self.slot_current_ask] = match[0]
        elif self.slot_current_ask == 'disk':
            dick_pattern = re.compile('\d+[GgTt]')
            match = re.match(dick_pattern, request)
            if match is not None and self.slot_current_ask not in nlu_slots:
                nlu_slots[self.slot_current_ask] = match[0]
                self.slotTable[self.slot_current_ask] = match[0]
        elif self.slot_current_ask == 'price':
            price_pattern = re.compile('\d+')
            match = re.match(price_pattern, request)
            if match is not None and self.slot_current_ask not in nlu_slots:
                nlu_slots[self.slot_current_ask] = match[0]
                self.slotTable[self.slot_current_ask] = match[0]

    def detect_slot_ask_answer(self, nlu_slots, request):
        """
        识别用户对某些slot:‘无所谓’、‘都行’、‘都可以’、‘没要求'、’无要求‘、’没什么要求‘
        :param request:
        :return:
        """
        if self.slot_current_ask in nlu_slots: # 识别出有值
            return None
        pattern = re.compile('((都行)|(无所谓)|(都可以)|(没要求)|(没什么要求)|(无要求))')
        match = re.search(pattern, request)
        if match is not None: # 识别成功
            self.slotTable[self.slot_current_ask] = config.SLOT_PLACE_HOLDER




    ###########################################
    # 状态转移条件函数集
    def init_state_transition(self, nlu_slots, request):
        """
        init转移状态
        :param nlu_slots:
        :param request:
        :return:
        """
        # 单独识别request
        self.detect_indent(request=request)

        # 用户不玩了
        if self.exit_flag == True:
            self.to_exit_ask()
        elif self.computer_flag == False:
            self.to_init()
        elif self.game_flag == 0 and self.review_flag == 0:
            self.to_slot_ask()
        elif self.game_flag == 1:
            self.to_game_ask()
        elif self.game_flag == 2:
            self.to_query()
        elif self.review_flag != 0:
            self.to_review_ask()
        else:
            print('Wrong in init state!!!')

    def chat_state_transition(self, nlu_slots, request):
        """
        这里做闲聊模块。待续
        :param nlu_slots:
        :param request:
        :return:
        """
        # Fixme

    def slot_ask_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        self.query_first = self.detect_query_first(request=request)

        if self.exit_flag == True:
            self.to_exit_ask()
        elif self.game_flag == 1:
            self.to_game_ask()
        elif self.game_flag == 2:  # 提到了某个游戏
            self.to_query()
        elif self.review_flag != 0 and len(self.slotRemain) == 0:  # 直接query
            self.to_query()
        elif self.review_flag != 0 and len(self.slotRemain) > 0:  # 直接query
            self.to_review_ask()
        elif len(self.slotRemain) == 0 or self.query_first == True:
            self.to_query()
        elif len(self.slotRemain) > 0:
            self.to_slot_ask()
        else:
            print('Wrong in slot ask state!!!')

    def review_ask_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        if self.exit_flag == True:
            self.to_exit_ask()
        elif self.game_flag == 1:
            self.to_game_ask()
        elif len(self.slotRemain) == 0 or self.query_first == True:
            self.to_query()
        elif len(self.slotRemain) > 0:
            self.to_slot_ask()
        else:
            print('Wrong in review ask state!!!')

    def game_ask_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        if self.exit_flag == True:
            self.to_exit_ask()
        elif self.game_flag == 1:  # 还是没提到任何游戏
            self.to_game_ask()
        elif self.detect_game_ask_conflict(nlu_slots=nlu_slots, request=request):  # 已有的slot的值，与游戏的最低配置矛盾，会提醒用户是否需要修改
            self.to_slot_confirm()
        elif self.game_flag == 2:  # 提到了具体游戏：
            self.to_query()
        else:
            print('Wrong in game_ask state!!!')

    def slot_confirm_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        # Fixme

    def query_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        self.query_change = False  # 进来时，需要重置这个值。
        product_change = self.detect_change_product_list(request)  # 检测用户是否想换一批产品
        self.slot_change_list = self.detect_slot_change(nlu_slots, request)  # 检测用户修改的slot
        ids = self.detect_choice(request=request)
        if self.exit_flag == True:
            self.to_exit_ask()
        elif product_change == True:  # 如果说，换一批
            self.query_change = True  # 用于返回
            self.to_query()
        elif len(self.slot_change_list) != 0:  # 检测到用户需要改slot,向用户确认
            self.slot_change = self.slot_change_list.pop()
            self.to_change_confirm()
        elif ids != -1 and ids <= 5:  # 因为最多显示五个
            self.buy_choice = ids
            self.to_buy()
        elif ids > 5 :
            self.to_query()  # 用户多选
        else:
            print('Wrong in query state')

    def change_confirm_state_transition(self, nlu_slots, request):
        """
        回答是或不是
        :param nlu_slots:
        :param request:
        :return:
        """
        slot = self.slot_change['slot_name']
        old_value = self.slot_change['old_value']
        new_value = self.slot_change['new_value']
        if '不是' in request.lower():  # 使用old值
            print('use old value!')
            self.slotTable[slot] = old_value
            if len(self.slot_change_list) > 0:  # 还有slot需要改
                self.slot_change = self.slot_change_list.pop()
                self.to_change_confirm()
            else:  # 改完了
                self.to_query()
        elif '是' in request.lower():
            print('use new value!')
            # 使用new值
            self.slotTable[slot] = new_value
            if len(self.slot_change_list) > 0:  # 还有slot需要改
                self.slot_change = self.slot_change_list.pop()
                self.to_change_confirm()
            else:  # 改完了
                self.to_query()
        else:  # 输入了其他
            self.to_change_confirm()

    def buy_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        choice = self.detect_buy_choice(request=request)
        if choice == 1:  # 如果买
            self.buy_done = True
            self.to_exit_ask()
        elif choice == 0:  # 不买
            self.to_exit_ask()
            self.buy_choice = -1 # 去掉了已经选择的
        else:
            print('Wrong in buy state')

    # def buy_done_state_transition(self, nlu_slots, request):
    #     """
    #     只是用于展示用户买的产品，直接转到exit_ask
    #     :param nlu_slots:
    #     :param request:
    #     :return:
    #     """
    #     self.to_exit_ask()

    def exit_ask_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """
        exit_choice = self.detect_exit_chocie(request=request)
        self.reset()
        if exit_choice == 1:  # 退出
            self.to_end()
        else:
            self.to_init()

    def end_state_transition(self, nlu_slots, request):
        """
        :param nlu_slots:
        :param request:
        :return:
        """


# 旧的Policy learner 类
# class Policy_learner():
#     """
#         这个policy learner，其实包含了state tracker，因为在这里记录整个对话过程中slot状态和采用的行为
#     """
#
#     def __init__(self):
#         self.slotTable = {slot_type: None for slot_type in config.SLOT_LIST}  # 初始化slot table
#         self.slotRemain = []
#         self.states = []
#         self.actions = []
#         self.state_tracker = State_machine()  # 这里用于获得当前对话系统所处的状态：是在询问？检索？还是购买？还是结束了？
#         # self.game_list = load_game_list('data_path')  #加载游戏列表
#         # self.game_list = ['英雄联盟', 'lol', '荒野求生', '吃鸡', 'gta', '玩游戏', '坦克大战']  # hard code for test
#         self.game_list = load_data.load_text_file('./data/game_list.txt')
#         self.game_request = []
#         self.review_label_list = pd.read_csv('./data/label_productId.csv', encoding='utf-8')['label'].tolist()
#         self.review_label_request = []
#
#     def learn_policy(self, nlu_slots, request):
#         """
#         学习整个当前对话系统应该采用的行为
#         :param nlu_slots: 从NLU中识别处关于slotTable中的值
#         :param request: 由于当前NLU只能识别处那几种值，但系统还需要用到根据当前状态做的一些识别：
#             1）ids：给出产品列表后，用户选择的编号
#             2）game：用户提出购买能玩相关游戏的模糊搜索需要识别的类型
#             3) buy_or_not: 用户选定相应产品时，询问用户是否确定购买
#             4）
#         :return:
#         """
#         current_state = self.state_tracker.state  # 获得当前state状态
#         self.actions.append(current_state)  # 记录当下状态
#         # Fixme：这里暂时使用最简单的用户体验流程
#         review_label = self.get_review_label(request)
#         self.update_review_label_request(review_label)
#         # Fixme: slot 和 game 之间的逻辑还没实现
#         if current_state in 'init':  # 判断走游戏模糊匹配还是走正常的电脑购买路线
#             game_request = self.get_game_request(request)
#             self.update_slot_Table(nlu_slots)  # 更新当前slot_table
#             self.update_game_list(game_request)  # 更新当前用户对游戏要求列表
#             # 更新状态机状态：假如有slot，也有game，则都转为game_ask
#             if self.is_game_request(request):
#                 if len(self.game_request) == 0:  # 没有提到游戏
#                     self.state_tracker.to_game_ask()
#                 else:
#                     self.state_tracker.to_game_query()
#             else:
#                 if len(self.slotRemain) == 0:
#                     self.state_tracker.to_slot_query()
#                 else:
#                     self.state_tracker.to_slot_ask()
#             # 更新系统状态
#             new_state = self.state_tracker.state
#             # 数据返回
#             return self.define_policy_return(new_state)
#
#         elif current_state == 'slot_ask':
#             # 更新当前系统状态
#             self.update_slot_Table(nlu_slots)
#
#             # 更新状态机
#             self.state_tracker.check_slot_ask_state(self.slotRemain)
#             new_state = self.state_tracker.state
#             return self.define_policy_return(new_state)
#
#         elif current_state == 'game_ask':
#             # 更新当前系统状态
#             game_request = self.get_game_request(request)
#             self.update_slot_Table(nlu_slots)
#             self.update_game_list(game_request)
#
#             # 更新状态机
#             self.state_tracker.check_game_ask_state(self.game_list)
#             new_state = self.state_tracker.state
#             return self.define_policy_return(new_state)
#
#         elif current_state == 'slot_query':
#             # Fixme:这里还有两种情况：1）用户修改slot；2）用户提出换一批产品
#             # 更新状态机
#             choice_id = self.detect_choice(request)  # 检查输入输入中是否包含数字
#             self.state_tracker.check_ask_query(choice_id)
#             new_state = self.state_tracker.state
#             return self.define_policy_return(new_state, ids=choice_id)
#
#         elif current_state == 'game_query':
#             # 更新状态机
#             choice_id = self.detect_choice(request)
#             self.state_tracker.check_game_query(choice_id)
#             new_state = self.state_tracker.state
#             return self.define_policy_return(new_state, ids=choice_id)
#
#         elif current_state == 'buy':
#             # 更改状态机状态
#             buy_choice = self.detect_buy_choice(request)
#             if buy_choice == 1:  # 如果买
#                 self.state_tracker.buy_done()
#             elif buy_choice == 0:  # 不买
#                 self.state_tracker.to_init()
#             self.reset()  # 买不买都重置slotTable
#             # 返回
#             new_state = self.state_tracker.state
#             return self.define_policy_return(new_state, ids=buy_choice)
#
#         elif current_state == 'end':
#             self.reset()
#             self.state_tracker.to_init()
#             new_state = self.state_tracker.state
#             return self.define_policy_return(new_state)
#         else:
#             print('State Wrong!')
#             exit(-1)
#
#     def reset(self):
#         """
#         用户重置用户需求：将原有slottable充值为None
#         :return:
#         """
#         self.slotTable = {slot_type: None for slot_type in config.SLOT_LIST}
#         self.game_request = []
#
#     def get_game_request(self, request):
#         """
#         判断request中，是否有提到游戏匹配。(规则）
#         :param request: 用户句子
#         :return: game_request list
#         """
#         game_request = []
#         for game in self.game_list:
#             game = game.lower()
#             request = request.lower()
#             start_index = request.find(game, 0)
#             if start_index != -1:
#                 game_request.append(game)  # 找到了一款游戏
#         return game_request
#
#     def get_review_label(self, request):
#         """
#         :param request:
#         :return:
#         """
#         # Fixme 这里暂时直接匹配
#         review_label = []
#         for label in self.review_label_list:
#             label = label.lower()
#             request = request.lower()
#             start_index = request.find(label, 0)
#             if start_index != -1:
#                 review_label.append(label)  # 找到一个label要求
#         return review_label
#
#     def is_game_request(self, request):
#         """
#         判断是否有游戏请求
#         :param request:
#         :return:
#         """
#         # Fixme
#         # 如果用户提到游戏列表中的游戏，则返回True
#         game_request = self.get_game_request(request)  # 获得当前存不存在游戏名字
#         self.update_game_list(game_request)  # 更新游戏列表
#         if len(game_request) > 0:
#             return True
#         game_rule = re.compile('玩游戏')
#         match = re.search(game_rule, request)
#         if match is not None:
#             start_index = match.start()
#             if start_index == 0 or request[start_index - 1] not in ['不', '少']:
#                 return True
#         return False
#
#     def is_review_tag(selff, request):
#         """
#         判断用户的句子，有没有给出关于电脑的一些标签。
#         如：【简单方便，轻薄精巧，小巧轻便】等
#         :param request:
#         :return:
#         """
#
#     def update_slot_Table(self, new_slot_table):
#         """
#         更新当前系统的slot_Table
#         :param new_slot_table:
#         :return:
#         """
#         # 处理价格问题
#         if 'price_m' in new_slot_table:
#             self.slotTable['price'] = new_slot_table['price_m']
#             del new_slot_table['price_m']
#         elif 'price_l' in new_slot_table:
#             if 'price_h' in new_slot_table:
#                 self.slotTable['price'] = (new_slot_table['price_l'] + new_slot_table['price_h']) / 2
#                 del new_slot_table['price_l']
#                 del new_slot_table['price_h']
#             else:
#                 self.slotTable['price'] = new_slot_table['price_l']
#                 del new_slot_table['price_l']
#         elif 'price_h' in new_slot_table:
#             if 'price_l' in new_slot_table:
#                 self.slotTable['price'] = (new_slot_table['price_h'] + new_slot_table['price_l']) / 2
#                 del new_slot_table['price_l']
#                 del new_slot_table['price_h']
#             else:
#                 self.slotTable['price'] = new_slot_table['price_h']
#                 del new_slot_table['price_l']
#         self.slotTable.update(new_slot_table)  # 更新当前的slotTalbel
#         current_state = [i for i, j in self.slotTable.items() if j is not None]
#         self.slotRemain = list(set(config.SLOT_NEEDED) - set(current_state))
#
#     def update_game_list(self, game_request):
#         """
#         更新当前用户对游戏的要求列表
#         :param game_request: list
#         :return:
#         """
#         self.game_request = list(set(self.game_request) | set(game_request))
#
#     def update_review_label_request(self, review_label):
#         self.review_label_request = list(set(self.review_label_request) | set(review_label))
#
#     def define_policy_return(self, state, **data):
#         """
#         根据不同的状态机的状态，返回不同的数据。
#         init : state, None
#         slot_ask : (state, slotTable)
#         game_ask : (state, game_list)
#         slot_query : (state, slotTable)
#         game_query : (state, game_list)
#         buy : (state, ids)
#         :param state: 当前系统状态
#         :param **data: 用于传入一些特殊的，需要返回的值
#         :return:
#         """
#         # print(state)
#         # print(data)
#         if state in ['init', 'end']:
#             return state, None
#         elif state in ['slot_ask', 'slot_query']:
#             return state, self.slotTable
#         elif state in ['game_ask', 'game_query']:
#             return state, self.game_list
#         elif state in ['buy']:
#             if 'ids' in data.keys():
#                 return state, data['ids']
#             else:
#                 print('输入数据有问题')
#                 return None
#                 exit(-1)
#
#     def detect_choice(self, request):
#         """
#         当self.flag 为True时，被执行
#         :param request:
#         :return: 选择的数字
#         """
#         assert self.state_tracker.state in ['slot_query', 'game_query']
#         pattern = re.compile('\d')
#         match = re.search(pattern, request)
#         if match:
#             ids = match[0]
#             return ids
#         return -1
#
#     def detect_buy_choice(self, request):
#         """
#         判断用户是否购买商品
#         :param request:
#         :return:
#         """
#         if '不是' in request.lower():
#             return 0
#         elif '是' in request.lower():
#             return 1
#         else:  # 不确定
#             return 0
#
#     def have_not_product(self):
#         """
#         没有检索到产品，需要改变系统状态吗？策略如何？
#         :return:
#         """
#         current_state = self.state_tracker.state  # 当前状态
#         if current_state == 'slot_query':  # 重新问下配置
#             # slot = random.sample(config.SLOT_NEEDED, 1)
#             # self.slotTable[slot] = None
#             self.state_tracker.to_slot_ask()
#             # Fixme
#         elif current_state == 'game_query':
#             # print()
#             self.state_tracker.to_game_ask()  # 换游戏？
#             # fixme
#         else:
#             print('系统状态出错')
#             exit(-1)

if __name__ == '__main__':
    state_machine = State_machine()
    print(state_machine.states)
    print(state_machine.name)
    print(state_machine.state)
    state_machine.test(10)
    print(state_machine.state)

    p = Policy_learner()
