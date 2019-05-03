# -*- coding: utf-8 -*-
from models.computer_.dialog_computer import Computer_Dialogue
from models.phone.dialog_phone import Phone_Dialogue
from models.camera.dialog_camera import Camera_Dialogue
from models.NLU.NLUService import NLUService
import numpy as np


def getRandomSentence(sentenceList):
    num = np.random.randint(len(sentenceList))
    return sentenceList[num]


class DialogManager:
    def __init__(self):
        self.domain = None
        self.dialog = None
        self.reponseText = ''
        self.nlu = NLUService()
        # self.dialogs = {'computer': Computer_Dialogue(), 'phone': Phone_Dialogue()}
        self.dialogs = {'phone': Phone_Dialogue(self.nlu), 'camera': Camera_Dialogue(self.nlu), 'computer': Computer_Dialogue(self.nlu)}

    def user(self, domain, sentence):
        print(domain)
        print(sentence)
        if not self.domain:
            self.domain = domain
            self.dialog = self.dialogs[domain]
        self.dialog.user(sentence)

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
        else:
            res = {}
            res['response'] = self.dialog.response()
            res['showResult'] = self.dialog.show_result
            res['slot_value'] = self.dialog.get_slot_table()
            res['result'] = self.dialog.get_result() if self.dialog.show_result else []
            return res

    def reset(self):
        if self.dialog is not None:
            self.dialog.reset()
            self.domain = None


if __name__ == '__main__':
    dialog = DialogManager()
    dialog.user('phone', "我要买手机")
    print("客服:", dialog.response())
    while True:
        inp = input("用户：")
        dialog.user('phone', inp)
        print("客服:", dialog.response())
