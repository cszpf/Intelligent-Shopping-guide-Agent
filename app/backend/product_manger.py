import pandas as pd
import load_data


class ProductManager:

    def __init__(self):
        """
        初始化，加载产品数据
        """
        # FixMe:暂时写死，
        self.product_brief_info = pd.read_csv('./data/jingdong_extract_attrs', encoding='utf-8')
        self.product_brands_list = load_data.load_text_file('./data/coumters_brands_list.txt')
        self.game_configurations_table = load_data.load_game_configurations('')

    def get_product_list(self, slot_list):  #, game_flag=False, game_list=None
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
        for i in range(len(slot_values)):
            slot_type = slot_types[i]
            slot_value = slot_values[i]
            if slot_type == 'price':
                theta = 500
                price_low = float(slot_value) - theta
                price_high = float(slot_value) + theta
                data = data[(data['price'] > price_low) & (data['price'] < price_high)]
            elif slot_type in ['brand', 'cpu', 'disk', 'memory', 'gpu']:
                # print(slot_type)
                # print(slot_value)
                # print(type(slot_value))
                # print(data.dtypes)

                data = data[data[slot_type].apply(lambda x: slot_value.lower() in str(x).lower())]

        length = len(data)
        if length == 0:
            return list()
        elif length > 5:  # 显示5个就好
            result = data[0:5].reset_index(drop=True)
            return result
        else:
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

    def get_game_product_list(self, game_request):
        """
        根据给出的游戏，找出配置符合这些游戏的电脑产品
        :param game_request: list 一系列游戏的配置要求
        :return:
        """
        # Fixme
        product_list = []
        game_config = self.get_configuration_requirements(game_request)
        higher_config = self.get_higher_config(game_config)

        return product_list




    def get_configuration_requirements(self, game_request):
        """
        根据给出的游戏列表，给出能满足所有游戏配置要求的电脑配置最低要求
        :param game_request:
        :return: dict{} 满足game_request中所有配置要求的最低配置
        """
        # Fixme

    def get_higher_config(self, config):
        """
        获得比输入配置更高配置
        :param config:
        :return:
        """
        # Fixme
        config_result = list()



from collections import Counter

if __name__ == '__main__':
    print('hello, 不要随便运行这个文件')
    product_brief_info = pd.read_csv('./data/jingdong_extract_attrs')
    print(product_brief_info.dtypes)
    cpu = product_brief_info['cpu'].values
    print(len(product_brief_info))
    print(Counter(cpu))
    print(Counter(product_brief_info['gpu']))
    data = product_brief_info.copy()
    slot_type = 'brand'
    slot_value = '联想'

    print(data.dtypes)
    data = data[data[slot_type].apply(lambda x: slot_value.lower() in str(x).lower())]

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
