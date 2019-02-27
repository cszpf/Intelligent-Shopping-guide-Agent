# -*- coding:utf-8 -*-
# 这里的NLU中slot filling 能识别出的slot list
SLOT_LIST = ['brand', 'memory', 'price', 'disk', 'cpu', 'gpu']
# 规定最少需要获取price、cpu和memory信息才能进行推荐
SLOT_NEEDED = ['brand', 'price', 'memory']
# 产品一次展示的数量
PRODUCT_SHOW_NUM = 5
# 检索时,价格的浮动查询
PRICE_THRESHOLD = 500
# slot_ask中,如果用户提到any_way,使用下面这个值填充
SLOT_PLACE_HOLDER = 'all_fine'