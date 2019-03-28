import pandas as pd
import load_data
import re
import os
import config

class ProductManager:

    def __init__(self):
        """
        初始化，加载产品数据
        """
        # FixMe:暂时写死，
        self.product_brief_info = pd.read_csv(
            os.path.join('data', 'jingdong_extract_attrs_add_part_laptop_with_id.csv'), encoding='utf-8').fillna('缺失')
        self.product_brands_list = load_data.load_text_file(os.path.join('data', 'coumters_brands_list.txt'))
        self.game_configurations_table = pd.read_csv(os.path.join('data', 'game_config.csv'), encoding='utf-8')
        self.review_product = pd.read_csv(os.path.join('data', 'label_productId.csv'), encoding='utf-8')

    def query(self, game_request, review_request, slotTable):
        """
        根据
        :param game_request:   游戏的要求
        :param review_request: Review_request要求
        :param slotTable:
        :return: 4个list
        """
        ###################
        # 定义回复的内容
        review_result = list()  # 产品id的list
        # game_result = list()  # 游戏id的list
        slotTable_resutl = list()  #

        ###################
        # 讲slotTable中的占位符,替换成None
        slot_table = {}
        for slot, value in slotTable.items():
            if value is not None and value != config.SLOT_PLACE_HOLDER:
                slot_table[slot] = value

        ###################
        # 体验的产品
        if len(review_request) > 0:
            id_str_list = self.review_product[self.review_product['label'].isin(review_request)]['productId'].tolist()
            for id_str in id_str_list:
                ids = eval(id_str)
                review_result.extend(ids)

        # 有提到游戏的检索
        product_list = pd.DataFrame()
        if len(game_request) > 0:
            game_config = self.get_configuration_requirements(game_request)
            all_suitable_config = self.get_higher_config(game_config)  # 获得所有可行配置
            for g_config in all_suitable_config:
                slotTable.update(g_config)  # 将游戏的slot,融入到slotTable中,
                products = self.get_product_list(slot_list=slot_table)
                product_list = product_list.append(products)
            product_list = product_list.reset_index(drop=True)
        else:
            product_list = self.get_product_list(slot_list=slot_table)
        # print('slot table product length: ', len(product_list))
        slotTable_resutl = product_list.to_dict('record')
        # 结合产品体验
        if len(product_list) > 0 and len(review_result) > 0:
            product_result = product_list[product_list['productId'].isin(review_result)].to_dict('record')
        else:
            product_result = slotTable_resutl

        return review_result, slotTable_resutl, product_result
        # slot_table

    def get_game_product_list(self, game_request):
        """
        根据给出的游戏，找出配置符合这些游戏的电脑产品
        :param game_request: list 一系列游戏的配置要求
        :return:
        """
        # Fixme
        product_list = pd.DataFrame()
        game_config = self.get_configuration_requirements(game_request)
        all_suitable_config = self.get_higher_config(game_config)  # 获得所有可行配置
        for config in all_suitable_config:
            products = self.get_product_list(slot_list=config)
            # print(type(products))
            # print(type(products))
            product_list = product_list.append(products)
        product_list = product_list.reset_index(drop=True)
        # if len(product_list) > 5:
        #     return product_list[0:5]
        return product_list

    def get_product_list(self, slot_list):  # , game_flag=False, game_list=None
        """
        根据slot_list的要求，选出一些产品
        :param slot_list:
        :return:
        """
        # if game_flag == True:
        #     game_slot_config = self.get_game_product_list(game_list)
        #     # Fixme
        slot_types = []
        slot_values = []
        for key, value in slot_list.items():
            if value is not None:
                slot_types.append(key)
                slot_values.append(value)
        data = self.product_brief_info.copy()
        # print(len(data))
        for i in range(len(slot_values)):
            slot_type = slot_types[i]
            slot_value = slot_values[i]
            if len(data) == 0:
                return pd.DataFrame()
            if slot_type == 'price':
                price_low = float(slot_value) - config.PRICE_THRESHOLD
                price_high = float(slot_value) + config.PRICE_THRESHOLD
                data = data[(data['price'] > price_low) & (data['price'] < price_high)]
            elif slot_type in ['brand', 'cpu', 'disk', 'memory', 'gpu']:
                data = data[data[slot_type].apply(lambda x: slot_value.lower() in str(x).lower())]
        result = data.reset_index(drop=True)
        return result

    def get_product(self, tag_name, tag_type):
        """
        根据具体的tag_type:['brand', 'memory', 'price', 'disk', 'cpu', 'gpu']来获得具体产品
        :param tag_name:
        :param tag_type:
        :return:
        """
        if tag_type == 'brand':  # 可能只是一个中文名,或英文名：
            data_result = self.product_brief_info[
                self.product_brief_info[tag_type].apply(lambda x: tag_name.lower() in x.lower())]
            return data_result

        elif tag_type == 'memory':
            data_result = self.product_brief_info[
                self.product_brief_info[tag_type].apply(lambda x: tag_name.lower() == x.lower())]
            return data_result

        elif tag_type == 'price':
            price_low = float(tag_name[0])
            price_hight = int(tag_name[1])
            theta = 500
            if price_low == price_hight:  # 如果是只有一个价格,人为设置一个浮动的价格
                price_low -= theta
                price_hight += theta
            data_result = self.product_brief_info[(self.product_brief_info['price'] > price_low) &
                                                  (self.product_brief_info['price'] < price_hight)]
            return data_result

        elif tag_type == 'disk':
            data_result = self.product_brief_info[
                self.product_brief_info[tag_type].apply(lambda x: tag_name.lower() == x.lower())]
            return data_result

        elif tag_type == 'cpu':
            data_result = self.product_brief_info[
                self.product_brief_info[tag_type].apply(lambda x: tag_name.lower() == x.lower())]
            return data_result

        elif tag_type == 'gpu':
            data_result = self.product_brief_info[
                self.product_brief_info[tag_type].apply(lambda x: tag_name.lower() == x.lower())]
            return data_result

    def get_configuration_requirements(self, game_request):
        """
        根据给出的游戏列表，给出能满足所有游戏配置要求的电脑配置最低要求
        :param game_request:
        :return: dict{} 满足game_request中所有配置要求的最低配置
        """
        # Fixme: 先考虑只有一款游戏
        max_cpu = None
        max_memory = None
        max_gpu = None
        game_configs = self.game_configurations_table[
            self.game_configurations_table['game_words'].isin(game_request)].reset_index(drop=True)
        for index, config in game_configs.iterrows():
            if index == 0:
                max_cpu = config['cpu']
                max_memory = config['memory']
                max_gpu = config['gpu']
                continue
            max_cpu = self.compare_cpu(max_cpu, config['cpu'])
            max_memory = self.compare_memory(max_memory, config['memory'])
            max_gpu = self.compare_gpu(max_gpu, config['gpu'])
        return {'cpu': max_cpu, 'memory': max_memory, 'gpu': max_gpu}

    def get_higher_config(self, config, num=5):
        """
        获得比输入配置更高配置
        :param config: 基础配置
        :param num: 设置最多选取多少个更高配置
        :return:
        """
        # Fixme
        GPU_I_LIST = [3, 5, 7]
        MEMORY_LIST = [2, 4, 8, 16, 32]
        GPU_GEN_LIST = [8, 9, 10]  # 同系列下的代数
        GPU_LIST = [5, 6, 7, 8, 9]  # 同代数下的强度
        config_result = list()
        config_result.append(config)

        # CPU
        # Fixme 这里没有考虑cpu中，同系列的不同代数
        cpu_ix_pattern = re.compile('[Ii]\d')
        cpu_ix_match = re.search(cpu_ix_pattern, config['cpu'])
        cpu_ix = int(cpu_ix_match[0][-1])
        for i in GPU_I_LIST:
            if i > cpu_ix:
                temp = config.copy()
                temp['cpu'] = 'i' + str(i)
                config_result.append(temp)

        # Memory
        memory_num = int(config['memory'].lower().split('g')[0])
        for i in MEMORY_LIST:
            if i > memory_num:
                temp = config.copy()
                temp['memory'] = str(i) + 'G'
                config_result.append(temp)

        # GPU
        # Fixme:这里只对当前gpu配置，找出其上一层的GPU，没有一直迭代上去，找处所有
        # 如：{GTX980} 找到了 {990 和 1080 } 但，找不到 1090，因为这里没有一直迭代上去。
        pattern = re.compile('\d{3,4}')  #
        gpu1_match = re.search(pattern, config['gpu'])
        gpu_num = gpu1_match[0]  # string
        # 代数
        current_gen = int(gpu_num[:-2])  # 如果三位，则选择第一个；如果四位，则选择前两位
        current_num = int(gpu_num[-2])  # 同一代中，的不同强度的系列
        # 代数
        for gen in GPU_GEN_LIST:
            if gen > current_gen:
                # new_gpu_num = gpu_num.replace(str(current_gen), str(gen))
                new_gpu_num = str(gen) + gpu_num[-2:]
                temp = config.copy()
                temp['gpu'] = config['gpu'].replace(gpu_num, new_gpu_num)
                config_result.append(temp)
            elif gen == current_gen:
                for num in GPU_LIST:  # 同一代中不同的强度
                    if num > current_num:
                        new_gpu_num = str(current_gen) + str(num) + gpu_num[-1]  # 重新拼接
                        temp = config.copy()
                        temp['gpu'] = config['gpu'].replace(gpu_num, new_gpu_num)

                        # config['gpu'] = config['gpu'].replace(gpu_num, new_gpu_num)
                        config_result.append(temp)
        return config_result

    def compare_cpu(self, cpu1, cpu2):
        """
        :param cpu1:
        :param cpu2:
        :return: 返回大的一个cpu
        """
        # Fixme：这里暂时只做到iX 这个比较，同一系列下的，暂时没有比较
        ix_pattern = re.compile('[Ii]\d')
        cpu1_ix = re.search(ix_pattern, cpu1)
        cpu2_ix = re.search(ix_pattern, cpu2)
        assert cpu1_ix is not None
        assert cpu2_ix is not None
        if int(cpu1_ix[0][-1]) > int(cpu2_ix[0][-1]):
            return cpu1
        return cpu2

    def compare_memory(self, memory1, memory2):
        """
        :param memory1:
        :param memory2:
        :return: 返回配置要求较高的一个
        """
        m1 = int(memory1.strip().lower().split('g')[0])
        m2 = int(memory1.strip().lower().split('g')[0])
        if m1 > m2:
            return memory1
        return memory2

    def compare_gpu(self, gpu1, gpu2):
        """
        :param gpu1:
        :param gpu2:
        :return:
        """
        # Fixme 当前游戏（办公）配置只有GTX系列的，没有设计其他厂商和系列的GPU。所以现在暂时只做gtx
        pattern = re.compile('\d{3,4}')  #
        gpu1_match = re.search(pattern, gpu1)
        gpu2_match = re.search(pattern, gpu2)
        assert gpu1_match is not None
        assert gpu2_match is not None
        if int(gpu1_match[0]) > int(gpu2_match[0]):
            return gpu1
        return gpu2


from collections import Counter

if __name__ == '__main__':
    print('hello, 不要随便运行这个文件')
    # product_brief_info = pd.read_csv('./data/jingdong_extract_attrs')
    # print(product_brief_info.dtypes)
    # cpu = product_brief_info['cpu'].values
    # print(len(product_brief_info))
    # print(Counter(cpu))
    # print(Counter(product_brief_info['gpu']))
    # data = product_brief_info.copy()
    # slot_type = 'brand'
    # slot_value = '联想'
    #
    # print(data.dtypes)
    # data = data[data[slot_type].apply(lambda x: slot_value.lower() in str(x).lower())]

    # print(product_brief_info.columns)
    # print(product_brief_info.head())
    # print(len(product_brief_info))
    #
    # p = './data/coumters_brands_list.txt'
    # t = load_data.load_text_file(p, 0)
    # print(type(t))
    # print(t)
    # suning = pd.read_json(path_or_buf='./data/suningComputers.json', orient='records')
    # print(type(suning))
    # print(suning.columns)
    # print(len(suning))

    test = ProductManager()
    config = {'cpu': 'i7', 'memory': '8G', 'gpu': 'GTX980ti'}
    config_higer = test.get_higher_config(config)
    for config in config_higer:
        print(config)
    # print(config_higer)
