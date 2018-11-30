import re
import random
import load_data
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


##############
# 这里的NLU中slot filling 能识别出的slot list
# Fixme: 这里可以使用配置文件，统一配置
slotList = ['brand', 'memory', 'price', 'disk', 'cpu', 'gpu']
# 规定最少需要获取price、cpu和memory信息才能进行推荐
# Fixme：这里的query条件有点粗暴，可以更改
slotneeded = ['brand', 'price', 'cpu']


class Policy_learner():
    """
        这个policy learner，其实包含了state tracker，因为在这里记录整个对话过程中slot状态和采用的行为
    """

    def __init__(self):
        self.slotTable = {slot_type: None for slot_type in slotList}  # 初始化slot table
        self.slotRemain = []
        self.states = []
        self.actions = []
        self.state_tracker = State_machine()  # 这里用于获得当前对话系统所处的状态：是在询问？检索？还是购买？还是结束了？
        # self.game_list = load_game_list('data_path')  #加载游戏列表
        # self.game_list = ['英雄联盟', 'lol', '荒野求生', '吃鸡', 'gta', '玩游戏', '坦克大战']  # hard code for test
        self.game_list = load_data.load_text_file('./data/game_list.txt')
        self.game_request = []

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
        current_state = self.state_tracker.state  # 获得当前state状态
        self.actions.append(current_state)  # 记录当下状态
        # Fixme: slot 和 game 之间的逻辑还没实现
        if current_state in 'init':  # 判断走游戏模糊匹配还是走正常的电脑购买路线
            print('init stae ::::::::::::')
            game_request = self.get_game_request(request)
            print(game_request)
            self.update_slot_Table(nlu_slots)  # 更新当前slot_table
            self.update_game_list(game_request)  # 更新当前用户对游戏要求列表
            print(self.slotTable)
            print(self.slotRemain)

            # 更新状态机状态：假如有slot，也有game，则都转为game_ask
            if self.is_game_request(request):
                if len(self.game_request) == 0:  # 没有提到游戏
                    self.state_tracker.to_game_ask()
                else:
                    self.state_tracker.to_game_query()
            else:
                if len(self.slotRemain) == 0:
                    self.state_tracker.to_slot_query()
                else:
                    self.state_tracker.to_slot_ask()
            # 更新系统状态
            new_state = self.state_tracker.state
            # 数据返回
            return self.define_policy_return(new_state)

        elif current_state == 'slot_ask':
            # 更新当前系统状态
            self.update_slot_Table(nlu_slots)

            # 更新状态机
            self.state_tracker.check_slot_ask_state(self.slotRemain)
            new_state = self.state_tracker.state
            return self.define_policy_return(new_state)

        elif current_state == 'game_ask':
            # 更新当前系统状态
            game_request = self.get_game_request(request)
            self.update_slot_Table(nlu_slots)
            self.update_game_list(game_request)

            # 更新状态机
            self.state_tracker.check_game_ask_state(self.game_list)
            new_state = self.state_tracker.state
            return self.define_policy_return(new_state)

        elif current_state == 'slot_query':
            # Fixme:这里还有两种情况：1）用户修改slot；2）用户提出换一批产品
            # 更新状态机
            choice_id = self.detect_choice(request)  # 检查输入输入中是否包含数字
            self.state_tracker.check_ask_query(choice_id)
            new_state = self.state_tracker.state
            return self.define_policy_return(new_state, ids=choice_id)

        elif current_state == 'game_query':
            # 更新状态机
            choice_id = self.detect_choice(request)
            self.state_tracker.check_game_query(choice_id)
            new_state = self.state_tracker.state
            return self.define_policy_return(new_state, ids=choice_id)

        elif current_state == 'buy':
            # 更改状态机状态
            buy_choice = self.detect_buy_choice(request)
            if buy_choice == 1:  # 如果买
                self.state_tracker.buy_done()
            elif buy_choice == 0:  # 不买
                self.state_tracker.to_init()
            self.reset()  # 买不买都重置slotTable
            # 返回
            new_state = self.state_tracker.state
            return self.define_policy_return(new_state, ids=buy_choice)

        elif current_state == 'end':
            self.reset()
            self.state_tracker.to_init()
            new_state = self.state_tracker.state
            return self.define_policy_return(new_state)
        else:
            print('State Wrong!')
            exit(-1)

    def reset(self):
        """
        用户重置用户需求：将原有slottable充值为None
        :return:
        """
        self.slotTable = {slot_type: None for slot_type in slotList}
        self.game_request = []

    def get_game_request(self, request):
        """
        判断request中，是否有提到游戏匹配。(规则）
        :param request: 用户句子
        :return: game_request list
        """
        game_request = []
        for game in self.game_list:
            game = game.lower()
            request = request.lower()
            start_index = request.find(game, 0)
            if start_index != -1:
                game_request.append(game)  # 找到了一款游戏
        return game_request

    def is_game_request(self, request):
        """
        判断是否有游戏请求
        :param request:
        :return:
        """
        # Fixme
        # 如果用户提到游戏列表中的游戏，则返回True
        game_request = self.get_game_request(request)  # 获得当前存不存在游戏名字
        self.update_game_list(game_request)  # 更新游戏列表
        if len(game_request) > 0:
            return True
        game_rule = re.compile('玩游戏')
        match = re.search(game_rule, request)
        if match is not None:
            start_index = match.start()
            if start_index == 0 or request[start_index - 1] not in ['不', '少']:
                return True
        return False

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
        self.slotRemain = list(set(slotneeded) - set(current_state))

    def update_game_list(self, game_request):
        """
        更新当前用户对游戏的要求列表
        :param game_request: list
        :return:
        """
        self.game_request = list(set(self.game_request) | set(game_request))

    def define_policy_return(self, state, **data):
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
        # print(state)
        # print(data)
        if state in ['init', 'end']:
            return state, None
        elif state in ['slot_ask', 'slot_query']:
            return state, self.slotTable
        elif state in ['game_ask', 'game_query']:
            return state, self.game_list
        elif state in ['buy']:

            if 'ids' in data.keys():

                return state, data['ids']
            else:
                print('输入数据有问题')
                return None
                exit(-1)

    def detect_choice(self, request):
        """
        当self.flag 为True时，被执行
        :param request:
        :return: 选择的数字
        """
        assert self.state_tracker.state in ['slot_query', 'game_query']
        pattern = re.compile('\d')
        match = re.search(pattern, request)
        if match:
            ids = match[0]
            return ids
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
        else:  # 不确定
            return 0

    def have_not_product(self):
        """
        没有检索到产品，需要改变系统状态吗？策略如何？
        :return:
        """
        current_state = self.state_tracker.state  # 当前状态
        if current_state == 'slot_query':  # 重新问下配置
            # slot = random.sample(slotneeded, 1)
            # self.slotTable[slot] = None
            self.state_tracker.to_slot_ask()
            # Fixme
        elif current_state == 'game_query':
            print()
            self.state_tracker.to_game_ask()  # 换游戏？
            # fixme
        else:
            print('系统状态出错')
            exit(-1)


if __name__ == '__main__':
    state_machine = State_machine()
    print(state_machine.states)
    print(state_machine.name)
    print(state_machine.state)
    state_machine.test(10)
    print(state_machine.state)

    p = Policy_learner()
