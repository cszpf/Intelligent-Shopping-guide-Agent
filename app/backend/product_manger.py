import pandas as pd
import load_data

class Product_maager:
    def __init__(self):
        """
        初始化，加载产品数据
        """
        # FixMe:暂时写死，
        self.product_brief_info = pd.read_csv('./data/jingdong_extract_attrs', encoding='utf-8')
        self.product_brands_list = load_data.load_text_file('./data/coumters_brands_list.txt')


    def get_product_list(self, slot_list):
        """
        根据slot_list的要求，选出一些产品
        :param slot_list:
        :return:
        """
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
                print(slot_type)
                print(slot_value)
                #print(type(slot_value))

                #print(data.dtypes)
                data = data[data[slot_type].apply(lambda x: slot_value.lower() in str(x).lower())]

        length = len(data)
        data.reset_index(drop=True, inplace=True)
        #print(data)
        if length == 0:
            return list()
        elif length > 5:  # 显示5个就好
            return data[0:5]
        else:
            return data


    def get_product(self, tag_name, tag_type):
        """
        根据具体的tag_type:['brand', 'memory', 'price', 'disk', 'cpu', 'gpu']来获得具体产品
        :param tag_name:
        :param tag_type:
        :return:
        """
        if tag_type == 'brand':   # 可能只是一个中文名,或英文名：
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

