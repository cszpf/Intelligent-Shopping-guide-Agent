# -*- coding: utf-8 -*-
from models.computer_.dialog_computer import Computer_Dialogue
from models.phone.dialog_phone import Phone_Dialogue
from models.camera.dialog_camera import Camera_Dialogue
from models.NLU.NLUService import NLUService
import numpy as np
from collections import defaultdict


def getRandomSentence(sentenceList):
    num = np.random.randint(len(sentenceList))
    return sentenceList[num]


def write_lines(file, lines):
    for line in lines:
        if type(line)!=str:
            continue
        file.write(line + '\n')
    file.close()


class DialogManager:
    def __init__(self):
        self.domain = None
        self.dialog = None
        self.reponseText = ''
        self.nlu = NLUService()
        # self.dialogs = {'computer': Computer_Dialogue(), 'phone': Phone_Dialogue()}
        self.dialogs = {'phone': Phone_Dialogue(self.nlu), 'camera': Camera_Dialogue(self.nlu),
                        'computer': Computer_Dialogue(self.nlu)}
        self.dialog_session = {}
        # error flag:用于判断是否应该向前端返回错误信息
        self.error_flag = {}
        # error_mark:没有抛出异常的逻辑错误
        self.error_mark = {}
        self.history = defaultdict(lambda: [])
        self.finish = {}
        self.record_history = False
        self.hello_flag = {}


    def save_log(self, token, type, reason=None):
        if not self.record_history:
            return
        if len(self.history[token]) == 0:
            return
        if token in self.error_mark:
            type = 'wrong'
        if token in self.error_flag:
            type = 'error'
        print("saving log of ", token)
        if type == 'error':
            history = self.history[token]
            history.insert(0, reason)
            history.append('')
            file = open('./dialog_logs/error.txt', 'a')
            write_lines(file, history)
            del self.history[token]
        else:
            history = self.history[token]
            history.append('')
            file = open('./dialog_logs/%s.txt' % type, 'a')
            write_lines(file, history)
            del self.history[token]

    def create_session(self, token):
        self.domain = None
        self.error_flag[token] = False
        self.finish[token] = False
        self.dialog_session[token] = {}
        self.error_mark[token] = False

    def load_session(self, token):
        if token in self.dialog_session:
            domain = self.dialog_session[token]['domain']
            self.domain = domain
            self.dialog = self.dialogs[domain]
            self.dialog.load(self.dialog_session[token]['model'])
        else:
            self.create_session(token)

    def user(self, domain, sentence, token):
        if domain == 'other' or domain == 'undefined':
            self.hello_flag[token] = True
            return
        if token in self.hello_flag:
            del self.hello_flag[token]
        self.load_session(token)
        print("domain:", domain)
        print("input:", sentence)
        self.history[token].append('user:' + sentence)
        if not self.domain:
            self.domain = domain
            self.dialog = self.dialogs[domain]
            self.dialog.reset()
        try:
            self.dialog.user(sentence)
            self.dialog_session[token] = {
                'domain': domain,
                'model': self.dialog.save()
            }
        except Exception as e:
            print("got an error in input")
            print(e)
            self.save_log(token, 'error', str(e))
            self.error_flag[token] = True
            # raise


    def hello(self):
        print("hello")
        sentenceList = ["你好，请问有什么可以帮到您吗？您可以通过导购助手挑选合适你的手机,电脑或者相机。",
                        "你好，请问需要什么服务？导购助手可以帮助您选购手机/电脑/相机。",
                        "你好，我可以帮你挑选手机/电脑/相机，请问你想买的是什么?"]
        return getRandomSentence(sentenceList)

    def return_error(self,token):
        res = {}
        sentence_list =  ['抱歉，系统似乎出现了点故障，重新操作试试？']
        res['response'] = getRandomSentence(sentence_list)
        res['showResult'] = False
        res['slot_value'] = {}
        res['error'] = False
        del self.error_flag[token]
        return res

    def response(self, token):
        if token in self.hello_flag and self.hello_flag[token]:
            res = {}
            res['response'] = self.hello()
            res['showResult'] = False
            res['slot_value'] = {}
            res['error'] = False
            return res
        if token in self.error_flag and self.error_flag[token]:
            return self.return_error(token)
        self.load_session(token)
        if self.domain is None:
            res = {}
            res['response'] = self.hello()
            res['showResult'] = False
            res['slot_value'] = {}
            res['error'] = False
            return res
        else:
            res = {}
            try:
                res['response'] = self.dialog.response()
                res['showResult'] = self.dialog.show_result
                res['slot_value'] = self.dialog.get_slot_table()
                res['result'] = self.dialog.get_result() if self.dialog.show_result else []
                res['error'] = False
                self.dialog_session[token] = {
                    'domain': self.domain,
                    'model': self.dialog.save()
                }
                self.history[token].append('server:' + res['response'])
                print(self.dialog.state)
                if self.dialog.finish:
                    self.save_log(token, 'success')
                    self.finish[token] = True
                    self.reset(token)
                    res['finish'] = True
            except Exception as e:
                print("got an error in output")
                print(e)
                self.save_log(token, 'error', str(e))
                self.error_flag[token] = True
                # raise
            if token in self.error_flag and self.error_flag[token]:
                return self.return_error(token)
            return res

    def reset(self, token):
        if token in self.dialog_session:
            if not self.finish[token]:
                self.save_log(token, 'stop')
            del self.dialog_session[token]
            del self.finish[token]
            del self.error_flag[token]
            del self.error_mark[token]

    def mark_error(self, token):
        if token not in self.dialog_session:
            return
        self.error_mark[token] = not self.error_mark[token]
        print("set error:", self.error_mark[token])


if __name__ == '__main__':
    dialog = DialogManager()
    dialog.user('phone', "我要买手机")
    print("客服:", dialog.response())
    while True:
        inp = input("用户：")
        dialog.user('phone', inp)
        print("客服:", dialog.response())
