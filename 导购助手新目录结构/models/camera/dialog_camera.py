import numpy as np
import sys
import os

sys.path.append(os.path.dirname(__file__))
from save_and_load import *
import json
import re
from static_data_camera import necessaryTag, labelToTag, ask_slot, listInfo, nameToColumn, adjustableSlot, \
    whatever_word, yes_word, no_word, func_synonyms, exp_synonyms, function_attr, brand_list
from collections import defaultdict
from search_camera import search_camera


def transNumber(num):
    digit = [str(i) for i in range(1, 10)]
    digit_char = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    if num in digit:
        return digit.index(num) + 1
    if num in digit_char:
        return digit_char.index(num) + 1
    return 'unkown'


def getRandomSentence(sentenceList):
    num = np.random.randint(len(sentenceList))
    return sentenceList[num]


def getChangeIntent(domain, sentence):
    changeableSlot = ['价格', '像素']
    posWord = ['贵', '高', '大', '好']
    negWord = ['便宜', '小', '低', '糟糕', '少', '差']
    positiveCount = 0
    target = ''
    # 匹配描述目标
    for word in changeableSlot:
        if word in sentence:
            target = word
            break
    # 补充目标
    if target == '':
        if any(w in sentence for w in ['贵', '便宜']):
            target = '价格'
        elif any(w in sentence for w in ['高', '低']):
            target = '价格?'

    tooWord = ['太', '有点', '过于', '不够']
    for word in posWord:
        if word in sentence:
            if all(w + word not in sentence for w in tooWord):
                positiveCount += 1
            else:
                positiveCount -= 1
    for word in negWord:
        if word in sentence:
            if all(w + word not in sentence for w in tooWord):
                positiveCount -= 1
            else:
                positiveCount += 1

    positive = 0
    if positiveCount > 0:
        positive = 1
    elif positiveCount < 0:
        positive = -1

    return (target, positive)


class Camera_Dialogue():
    def __init__(self, nlu):
        self.slot_value = {}
        self.state = "init"
        self.last_state = 'init'
        self.ask_slot = ""
        self.expected = ''
        self.resultList = None
        self.choice = {}
        self.morewhat = None
        self.responsePrefix = ''
        self.show_result = False
        self.finish = False
        self.nlu = nlu
        self.asked = []

    def save(self):
        model = {
            'slot_value': self.slot_value,
            'state': self.state,
            'ask_slot': self.ask_slot,
            'expected': self.expected,
            'attention': self.attention,
            'list_': self.list,
            'add_attention': self.add_attention,
            'choice': self.choice,
            'morewhat': self.morewhat,
            'asked': self.asked
        }
        return json.dumps(model)

    def load(self, model):
        m = json.loads(model)
        self.slot_value = m['slot_value']
        self.state = m['state']
        self.ask_slot = m['ask_slot']
        self.expected = m['expected']
        self.attention = m['attention']
        self.list = m['list_']
        self.add_attention = m['add_attention']
        self.choice = m['choice']
        self.morewhat = m['morewhat']
        self.asked = m['asked']

    def reset(self):
        self.slot_value = {}
        self.state = "init"
        self.last_state = 'init'
        self.ask_slot = ""
        self.expected = ''
        self.resultList = None
        self.choice = {}
        self.morewhat = None
        self.responsePrefix = ''
        self.show_result = False
        self.finish = False
        self.asked = []

    def changeState(self, state, lastState=None):
        print("state change to:" + state)
        if lastState is None:
            self.last_state = self.state
        else:
            self.last_state = lastState
        if state in ['result', 'confirmChoice']:
            self.show_result = True
        else:
            self.show_result = False
        self.state = state

    def goLastState(self):
        print("state go back to:" + self.last_state)
        self.state = self.last_state

    def user(self, sentence):
        sentence = sentence.strip()
        self.responsePrefix = ''
        if self.state == 'init':
            self.init(sentence)
        elif self.state == 'ask':
            self.ask(sentence)
        elif self.state == 'result':
            self.result(sentence)
        elif self.state == 'confirmChoice':
            self.confirmChoice(sentence)
        elif self.state == 'adjustConfirm':
            self.adjustConfirm(sentence)

    def listSlot(self, sentence):
        pass

    def doAdjust(self, morewhat):
        '''
        morewhat:('价格',1)
        '''
        print(morewhat)
        result = self.getResult()
        print(result)
        if morewhat[0] in adjustableSlot:
            upper = max([item[adjustableSlot[morewhat[0]]] for item in result if adjustableSlot[morewhat[0]] in item])
            lower = min([item[adjustableSlot[morewhat[0]]] for item in result if adjustableSlot[morewhat[0]] in item])
            if morewhat[1] > 0:
                self.slot_value[morewhat[0]] = [(upper, '>=')]
            else:
                self.slot_value[morewhat[0]] = [(lower, '<=')]
        self.changeState('result')

    def adjustConfirm(self, sentence):
        targetWord = ['价格', '像素']
        for word in targetWord:
            if word in sentence:
                self.morewhat = (word, self.morewhat[1])
                self.changeState('doAdjust')
                self.doAdjust(self.morewhat)
        intent = self.nlu.intention_predict(sentence)
        if intent == 'answer_yes':
            self.morewhat = (self.expected, self.morewhat[1])
            self.changeState('doAdjust')
            self.doAdjust(self.morewhat)
        elif intent == 'answer_slot':
            tag = self.extract(sentence)
            answer_intent = self.nlu.requirement_predict(sentence)
            negative = False
            if answer_intent == 'no_need':
                negative = True
            to_add = self.fillMessage(tag, negative)
            if answer_intent == 'whatever' and self.ask_slot:
                to_add[self.ask_slot] = [('whatever', '=')]
            if len(to_add) > 0:
                self.write(to_add)
                self.changeState('result')

    def confirmChoice(self, sentence):
        intent = self.nlu.intention_predict(sentence)
        if intent == 'answer_yes':
            self.changeState('done')
            return
        elif intent == 'answer_no':
            self.changeState('result')
            return
        for word in no_word:
            if word in sentence:
                self.changeState('result')
                return
        for word in yes_word:
            if word in sentence:
                self.changeState('done')
                return

    def result(self, sentence):
        if self.checkChoice(sentence):
            self.changeState('done')
            return
        tag = self.extract(sentence)
        intent = self.nlu.requirement_predict(sentence)
        print(sentence, intent)
        print(tag)
        if len(tag) > 0:
            tag = self.nlu.confirm_slot(tag, sentence)
            to_add = self.fillMessage(tag)
            self.write(to_add)

        morewhat = getChangeIntent('camera', sentence)
        if morewhat[1] != 0:
            if '?' in morewhat[0]:
                self.changeState('adjustConfirm')
                self.morewhat = morewhat
            elif morewhat[0] != '':
                self.changeState('doAdjust')
                self.doAdjust(morewhat)

    def response(self):
        if self.state == 'ask':
            # 检查必须的slot_value，如果没有的话就发出提问
            unasked = []
            for slot in necessaryTag:
                if slot not in self.asked:
                    unasked.append(slot)
            if len(unasked) > 0:
                num = np.random.randint(len(unasked))
                slot = unasked[num]
                self.ask_slot = slot
                return getRandomSentence(ask_slot[slot])
            # 如果到了这里，说明所有的slot都问完了,转入confirm_result
            else:
                self.changeState('confirm_result')
                return self.response()

        if self.state == 'list':
            self.changeState('ask')
            if self.ask_slot == '':
                return self.response()
            return getRandomSentence(listInfo[self.ask_slot])

        if self.state == 'result':
            res = self.search(self.slot_value)
            self.resultList = res
            if len(res) == 0:
                sentenceList = ["暂时没找到合适的商品哦，换个条件试试?"]
                return getRandomSentence(sentenceList)
            sentenceList = ["为您推荐以下商品,可回复第几个进行选择"]
            return getRandomSentence(sentenceList)

        if self.state == 'adjustConfirm':
            target = self.morewhat[0].replace('?', '')
            if target == '价格':
                self.expected = '价格'
                if self.morewhat[1] <= 0:
                    return getRandomSentence(["请问您是需要更贵的产品吗?"])
                else:
                    return getRandomSentence(["请问您是需要更便宜的产品吗?"])

        if self.state == 'confirmChoice':
            sentenceList = ["即将为您预订以下商品，是否确认？"]
            return getRandomSentence(sentenceList)

        if self.state == 'done':
            sentenceList = ["本次服务已结束，谢谢您的使用"]
            self.finish = True
            self.reset()
            return getRandomSentence(sentenceList)

    def doChoice(self):
        self.list = [self.choice]

    def checkNecessary(self):
        for tag in necessaryTag:
            if tag not in self.asked:
                return False
        return True

    def ask(self, sentence):
        intent = self.nlu.intention_predict(sentence)
        if intent == 'ask_slot_list':
            self.changeState('list')
            self.listSlot(sentence)
        else:
            tag = self.extract(sentence)
            intent = self.nlu.requirement_predict(sentence)
            print(sentence, intent)
            print(tag)
            if len(tag) == 0 and intent == 'whatever':
                if self.ask_slot != '':
                    self.write({self.ask_slot: [('whatever', '=')]})
                    self.asked.append(self.ask_slot)
                    self.ask_slot = ''
            else:
                tag = self.nlu.confirm_slot(tag, sentence)
                to_add = self.fillMessage(tag)
                self.write(to_add)
            if self.checkNecessary():
                self.changeState('result')

    def init(self, sentence):
        self.responsePrefix = '欢迎来到相机导购助手！'
        self.changeState('ask')
        self.ask(sentence)

    def chose(self, sentence):
        pass

    def filterNum(self, s):
        match = re.search(r'(\d+)', s)
        if match:
            return float(match.group(1))
        else:
            return -1

    def fillMessage(self, tag):
        # 主要用于修正tag和转换存储格式
        '''
        input:
            [{'type': 'pixel_m', 'word': '我要3000万像素的'}]
        output:
            {'像素':[(3000,'=')]}
        '''
        print("fillmessage")
        print(tag)
        if len(tag) == 0:
            return {}
        res = defaultdict(lambda: [])
        # entities = tag['entities']
        opDict = {'l': '>=', 'm': '=', 'u': '<='}
        bi_tag = ['brand', 'experience', 'function', 'frame', 'type', 'level']
        for t in tag:
            op = '='
            if t['type'] in bi_tag:
                name = labelToTag[t['type']]
                if t['need']:
                    res[name].append((t['word'], '='))
                else:
                    res[name].append((t['word'], '!='))
            else:
                if t['type'].find('_') != -1:
                    name_ = t['type'].split('_')
                    name = name_[0]
                    op = opDict[name_[1]]
                value = self.filterNum(t['word'])
                if value > 0:
                    res[labelToTag[name]].append((value, op))
        res = dict(res)
        print(res)
        return res

    def write(self, table):
        # table：待写入的slot-value
        print("write")
        print(table)
        for t in table:
            if t == self.ask_slot:
                self.asked.append(self.ask_slot)
                self.ask_slot = ''
            self.slot_value[t] = table[t]
            self.asked.append(t)

    def checkChoice(self, sentence):
        # 1. 通过第几个的方式来选择 #目前只支持这一种
        if len(self.resultList) == 0:
            return False
        pattern = re.compile('^([一二三四五12345])$')
        m = pattern.search(sentence)
        if (m):
            index = transNumber(m.group(1))
            if index > len(self.list):
                return False
            if '倒数' in sentence or '最后' in sentence:
                index = -index
            if index > 0:
                self.choice = self.resultList[index - 1]
            else:
                self.choice = self.resultList[index]
            return True

        pattern = re.compile('[第|最后]([一二三四五12345])')
        m = pattern.search(sentence)
        if m:
            index = transNumber(m.group(1))
            if index > len(self.resultList):
                return False
            if '倒数' in sentence or '最后' in sentence:
                index = -index
            if index > 0:
                self.choice = self.resultList[index - 1]
            else:
                self.choice = self.resultList[index]
            return True
        else:
            intent = self.nlu.requirement_predict(sentence)
            if intent == 'whatever':
                self.choice = self.resultList[0]
                return True
            else:
                for word in whatever_word:
                    if word in sentence:
                        self.choice = self.resultList[0]
                        return True
                return False

    def extract(self, sentence):
        print("extract")
        tag = self.nlu.camera_slot_predict(sentence)['entities']
        tag = [item for item in tag if item['type'] != 'brand' or item['word'] in brand_list]
        for word in exp_synonyms:
            if word in sentence:
                tag.append({'type': 'experience', 'word': word})
        for word in func_synonyms:
            if word in sentence:
                tag.append({'type': 'function', 'word': word})
        return tag

    def search(self, slot_value_table):
        # 调用这个函数进行数据库查询
        condition = slot_value_table
        result = search_camera(condition)
        self.resultList = result

        return result[0:5]

    def getResult(self):
        returnSlot = ['name', 'price', 'type', 'level', 'pixel', 'screen', 'shutter']
        res = []
        resultList = self.resultList
        if self.state == 'confirmChoice':
            resultList = [self.choice]
        for item in resultList:
            temp = {}
            itemDict = item.__dict__
            for key in itemDict:
                if key in returnSlot:
                    if type(itemDict[key]) == float:
                        temp[key] = itemDict[key]
                    elif itemDict[key] is not None:
                        temp[key] = itemDict[key]

            res.append(temp)
        return res

    def getSlotValue(self):
        res = {}
        opDict = {'<=': '小于', '=': '', '>=': '大于', '!=': '不要'}
        for slot in self.slot_value:
            if slot == '体验要求':
                continue
            sentenceList = []
            for con in self.slot_value[slot]:
                sentenceList.append(opDict[con[1]] + str(con[0]))
            slot = nameToColumn[slot]
            res[slot] = ','.join(sentenceList)

        if '体验要求' in self.slot_value:
            sentenceList = []
            for word in self.slot_value['体验要求']:
                sentenceList.append(word[0])
            res['experience'] = ','.join(sentenceList)

        if '功能要求' in self.slot_value:
            sentenceList = []
            for word in self.slot_value['功能要求']:
                sentenceList.append(word[0])
            res['function'] = ','.join(sentenceList)
        return res

    def get_slot_table(self):
        return self.getSlotValue()

    def get_result(self):
        return self.getResult()


if __name__ == '__main__':
    model = ()
    inp = "我要买个相机"
    print('用户：' + inp)
    model.user(inp)
    print("模型：", model.response())
