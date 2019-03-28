# 这里使用相对路径来导入包
from .NLU.nlu_interface import getIntent



class dialog_phone:
    def __init__(self):
        # 标志当前回复是否为展示查询结果的布尔值
        self.show_result = False
        pass
    
    def user(self,sentence):
        # 用户输入一句话会调用这个函数，sentence是用户输入的文本
        pass
    
    def response(self):
        # 调用这个函数来获得当前轮的回复，返回一个字符串
        pass
    
    def get_slot_value(self):
        # 调用这个函数来获得当前的slot table
        pass
    
    def get_result(self):
        # 调用这个函数来获得当前的数据库查询结果
        pass
    
    
if __name__ == "__main__":
    dialog = dialog_phone()