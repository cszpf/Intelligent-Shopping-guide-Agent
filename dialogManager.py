# -*- coding: utf-8 -*-
from prototype_phone import phoneDialog
from app.backend.dialogue import Computer_Dialogue
import numpy as np

def getRandomSentence(sentenceList):
    num = np.random.randint(len(sentenceList))
    return sentenceList[num]

class DialogManager:
    def __init__(self):
        self.domain = None
        self.dialog = None
        self.reponseText = ''
        
    def user(self,domain,sentence):
        print(domain)
        print(sentence)
        if not self.domain:
            self.domain = domain
            if domain == 'phone':
                self.dialog = phoneDialog()
            elif domain == 'computer':
                self.dialog = Computer_Dialogue()
        if self.domain == 'phone':
            self.dialog.user(sentence)
        elif self.domain == 'computer':
            self.responseText = self.dialog.get_response(sentence)
                
    
    def hello(self):
        print("hello")
        sentenceList = ["你好，请问有什么可以帮到您吗？您可以通过导购助手挑选合适你的手机,电脑或者相机。",
            "你好，请问需要什么服务？导购助手可以帮助您选购手机/电脑/相机。",
            "你好，我可以帮你挑选手机/电脑/相机，请问你想买的是什么?"]
        return getRandomSentence(sentenceList)
    
    def response(self):
        if self.domain is None:
            res = {}
            res['response'] = self.hello()
            res['showResult'] = False
            res['slot_value'] = {}
            return res
        elif self.domain == 'phone':
            res = {}
            res['response'] = self.dialog.response()
            res['showResult'] = self.dialog.showResult
            res['slot_value'] = self.dialog.getSlotValue()
            res['result'] = self.dialog.getResult() if self.dialog.showResult else []
            return res
        elif self.domain == 'computer':
            res = {}
            res['response'] = self.responseText
            res['showResult'] = self.dialog.show_result
            res['slot_value'] = self.dialog.get_slot_table()
            
            res['result'] = self.dialog.get_result() if self.dialog.show_result else []
            print(res['response'])
            print(res['showResult'])
            print(res['slot_value'])
            return res
    
    def reset(self):
        if self.dialog is not None:
            self.dialog.reset()
            self.domain = None
            

if __name__ == '__main__':
    dialog = DialogManager()
    dialog.user('computer',"我要买电脑")
    print("客服:",dialog.response())
    while True:
        inp = input("用户：")
        dialog.user('computer',inp)
        print("客服:",dialog.response())
    