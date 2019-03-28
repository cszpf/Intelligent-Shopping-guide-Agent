class NLU:
    # 在这个类中实现必要的nlu接口
    def __init__(self):
        pass
    
    def getIntent(self,sentence):
        return "phone"
    
# 全局声明一个类，方便多次调用
nlu = NLU()

def getIntent(sentence):
    # 直接使用已经加载好的模型进行预测
    return nlu.getIntent(sentence)


if __name__ == "__main__":
    print(getIntent("我要买手机"))