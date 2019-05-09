import numpy as np
import sys
import os

sys.path.append(os.path.dirname(__file__))
from save_and_load import *
import json
import re
from static_data_phone import necessaryTag, labelToTag, ask_slot, listInfo, nameToColumn, adjustableSlot, \
    whatever_word, yes_word, no_word, func_synonyms, exp_synonyms, function_attr, brand_list
from collections import defaultdict
from search_phone import searchPhone


def trans_number(num):
    '''
    transfer chinese number to 1-9
    :param num:number string
    :return:transfered number string
    '''
    digit = [str(i) for i in range(1, 10)]
    digit_char = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    if num in digit:
        return digit.index(num) + 1
    if num in digit_char:
        return digit_char.index(num) + 1
    return 'unkown'


def get_random_sentence(sentence_list):
    '''
    select a sentence randomly
    :param sentence_list:
    :return: selected sentence
    '''
    num = np.random.randint(len(sentence_list))
    return sentence_list[num]


def get_change_intent(domain, sentence):
    '''
    check if the input contains a change intention
    :param domain:current domain
    :param sentence:user input
    :return:(target,positive) a tuple contains a change target and a value to measure whether to change
    '''
    changeable_slot = ['价格', '硬盘', '内存', '像素', '尺寸']
    pos_word = ['贵', '高', '大', '好']
    neg_word = ['便宜', '小', '低', '糟糕', '少', '差']
    positive_count = 0
    target = ''
    # 匹配描述目标
    for word in changeable_slot:
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
    for word in pos_word:
        if word in sentence:
            if all(w + word not in sentence for w in tooWord):
                positive_count += 1
            else:
                positive_count -= 1
    for word in neg_word:
        if word in sentence:
            if all(w + word not in sentence for w in tooWord):
                positive_count -= 1
            else:
                positive_count += 1

    positive = 0
    if positive_count > 0:
        positive = 1
    elif positive_count < 0:
        positive = -1

    return (target, positive)


class Phone_Dialogue():
    def __init__(self, nlu):
        self.slot_value = {}
        self.state = "init"
        self.last_state = 'init'
        self.ask_slot = ""
        self.expected = ''
        self.result_list = None
        self.choice = {}
        self.morewhat = None
        self.show_result = False
        self.finish = False
        self.nlu = nlu
        self.asked = []

    def save(self):
        '''
        save current model to a json file
        :return: json string
        '''
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
        '''
        load model from json string
        :param model:json string
        :return:None
        '''
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
        '''
        reset a dialog state
        :return:None
        '''
        self.slot_value = {}
        self.state = "init"
        self.last_state = 'init'
        self.ask_slot = ""
        self.expected = ''
        self.result_list = None
        self.choice = {}
        self.morewhat = None
        self.show_result = False
        self.finish = False
        self.asked = []

    def change_state(self, state, last_state=None):
        '''
        change dialog state
        :param state:next state
        :param last_state:current state
        :return:None
        '''
        print("state change to:" + state)
        if last_state is None:
            self.last_state = self.state
        else:
            self.last_state = last_state
        if state in ['result', 'confirm_choice']:
            self.show_result = True
        else:
            self.show_result = False
        self.state = state

    def go_last_state(self):
        '''
        go back to last dialog state
        :return:None
        '''
        print("state go back to:" + self.last_state)
        self.state = self.last_state

    def user(self, sentence):
        '''
        deal with user input, routing input to different state
        :param sentence:user input
        :return:None
        '''
        sentence = sentence.strip()
        if self.state == 'init':
            self.init(sentence)
        elif self.state == 'ask':
            self.ask(sentence)
        elif self.state == 'result':
            self.result(sentence)
        elif self.state == 'confirm_choice':
            self.confirm_choice(sentence)
        elif self.state == 'adjust_confirm':
            self.adjust_confirm(sentence)

    def list_slot(self, sentence):
        '''
        list informable slot,empty for input
        :param sentence:sentence
        :return:None
        '''
        pass

    def do_adjust(self, morewhat):
        '''
        excute an adjustion
        :param morewhat:(target,positive) : ('价格',1) ,positive>0 means adjust higher value
        :return:None
        '''
        print(morewhat)
        result = self.get_result()
        print(result)
        if morewhat[0] in adjustableSlot:
            upper = max([item[adjustableSlot[morewhat[0]]] for item in result if adjustableSlot[morewhat[0]] in item])
            lower = min([item[adjustableSlot[morewhat[0]]] for item in result if adjustableSlot[morewhat[0]] in item])
            if morewhat[1] > 0:
                self.slot_value[morewhat[0]] = [(upper, '>=')]
            else:
                self.slot_value[morewhat[0]] = [(lower, '<=')]
        self.change_state('result')

    def adjust_confirm(self, sentence):
        '''
        confirm adjustion for uncertained input
        :param sentence: user input
        :return: None
        '''
        targetWord = ['价格', '像素', '尺寸', '硬盘', '内存']
        for word in targetWord:
            if word in sentence:
                self.morewhat = (word, self.morewhat[1])
                self.change_state('do_adjust')
                self.do_adjust(self.morewhat)
        intent = self.nlu.intention_predict(sentence)
        if intent == 'answer_yes':
            self.morewhat = (self.expected, self.morewhat[1])
            self.change_state('do_adjust')
            self.do_adjust(self.morewhat)
        elif intent == 'answer_slot':
            tag = self.extract(sentence)
            answer_intent = self.nlu.requirement_predict(sentence)
            negative = False
            if answer_intent == 'no_need':
                negative = True
            to_add = self.fill_message(tag, negative)
            if answer_intent == 'whatever' and self.ask_slot:
                to_add[self.ask_slot] = [('whatever', '=')]
            if len(to_add) > 0:
                self.write(to_add)
                self.change_state('result')

    def confirm_choice(self, sentence):
        '''
        confirm the result the user chosed
        :param sentence: user input
        :return:None
        '''
        intent = self.nlu.intention_predict(sentence)
        if intent == 'answer_yes':
            self.change_state('done')
            return
        elif intent == 'answer_no':
            self.change_state('result')
            return
        for word in no_word:
            if word in sentence:
                self.change_state('result')
                return
        for word in yes_word:
            if word in sentence:
                self.change_state('done')
                return

    def result(self, sentence):
        '''
        check user's reponse to the result
        :param sentence:user input
        :return:None
        '''
        if self.check_choice(sentence):
            self.change_state('done')
            return
        tag = self.extract(sentence)
        intent = self.nlu.requirement_predict(sentence)
        print(sentence, intent)
        print(tag)
        if len(tag) > 0:
            tag = self.nlu.confirm_slot(tag, sentence)
            to_add = self.fill_message(tag)
            self.write(to_add)

        morewhat = get_change_intent('phone', sentence)
        if morewhat[1] != 0:
            if '?' in morewhat[0]:
                self.change_state('adjust_confirm')
                self.morewhat = morewhat
            elif morewhat[0] != '':
                self.change_state('do_adjust')
                self.do_adjust(morewhat)

    def response(self):
        '''
        NLG module,generating response according to current state
        :return:dialog response
        '''
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
                return get_random_sentence(ask_slot[slot])
            # 如果到了这里，说明所有的slot都问完了,转入confirm_result
            else:
                self.change_state('confirm_result')
                return self.response()

        if self.state == 'list':
            self.change_state('ask')
            if self.ask_slot == '':
                return self.response()
            return get_random_sentence(listInfo[self.ask_slot])

        if self.state == 'result':
            res = self.search(self.slot_value)
            self.result_list = res
            if len(res) == 0:
                sentence_list = ["暂时没找到合适的商品哦，换个条件试试?"]
                return get_random_sentence(sentence_list)
            sentence_list = ["为您推荐以下商品,可回复第几个进行选择"]
            return get_random_sentence(sentence_list)

        if self.state == 'adjust_confirm':
            target = self.morewhat[0].replace('?', '')
            if target == '价格':
                self.expected = '价格'
                if self.morewhat[1] <= 0:
                    return get_random_sentence(["请问您是需要更贵的产品吗?"])
                else:
                    return get_random_sentence(["请问您是需要更便宜的产品吗?"])

        if self.state == 'confirm_choice':
            sentence_list = ["即将为您预订以下商品，是否确认？"]
            return get_random_sentence(sentence_list)

        if self.state == 'done':
            sentence_list = ["本次服务已结束，谢谢您的使用"]
            self.finish = True
            self.reset()
            return get_random_sentence(sentence_list)

    def do_choice(self):
        '''
        select a result
        :return:None
        '''
        self.list = [self.choice]

    def check_necessary(self):
        '''
        check if all the necessary tag is asked
        :return:True / False
        '''
        for tag in necessaryTag:
            if tag not in self.asked:
                return False
        return True

    def ask(self, sentence):
        '''
        check user response for a asking action
        :param sentence:user input
        :return:None
        '''
        intent = self.nlu.intention_predict(sentence)
        if intent == 'ask_slot_list':
            self.change_state('list')
            self.list_slot(sentence)
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
                to_add = self.fill_message(tag)
                self.write(to_add)
            if self.check_necessary():
                self.change_state('result')

    def init(self, sentence):
        '''
        init state
        :param sentence:user input
        :return:None
        '''
        self.change_state('ask')
        self.ask(sentence)

    def chose(self, sentence):
        pass

    def filterNum(self, s):
        '''
        check if string contains continuous number
        :param s:
        :return:
        '''
        match = re.search(r'(\d+)', s)
        if match:
            return float(match.group(1))
        else:
            return -1

    def fill_message(self, tag):
        '''
        transfer the tag format
        :param tag:[{'type': 'pixel_m', 'word': '我要3000万像素的'}]
        :return:{'像素':[(3000,'=')]}
        '''
        print("fill_message")
        print(tag)
        if len(tag) == 0:
            return {}
        res = defaultdict(lambda: [])
        # entities = tag['entities']
        op_dict = {'l': '>=', 'm': '=', 'u': '<='}
        bi_tag = ['brand', 'experience', 'function']
        for t in tag:
            op = '='
            if t['type'] in bi_tag:
                name = labelToTag[t['type']]
                if t['need']:
                    res[name].append((t['word'], '='))
                else:
                    res[name].append((t['word'], '!='))
            else:
                t['type'] = t['type'].replace('memory_size', 'memory')
                t['type'] = t['type'].replace('ram', 'memory')
                if t['type'].find('_') != -1:
                    name_ = t['type'].split('_')
                    name = name_[0]
                    op = op_dict[name_[1]]
                value = self.filterNum(t['word'])
                if value > 0:
                    res[labelToTag[name]].append((value, op))
        res = dict(res)
        print(res)
        return res

    def write(self, table):
        '''
        write slot-value-pair to slot table
        :param table:{'像素':[(3000,'=')]}
        :return:None
        '''
        # table：待写入的slot-value
        print("write")
        print(table)
        for t in table:
            if t == self.ask_slot:
                self.asked.append(self.ask_slot)
                self.ask_slot = ''
            self.slot_value[t] = table[t]
            self.asked.append(t)

    def check_choice(self, sentence):
        '''
        check which result user chose
        :param sentence: user input
        :return:result index
        '''
        # 1. 通过第几个的方式来选择 #目前只支持这一种
        if len(self.result_list) == 0:
            return False
        pattern = re.compile('^([一二三四五12345])$')
        m = pattern.search(sentence)
        if (m):
            index = trans_number(m.group(1))
            if index > len(self.list):
                return False
            if '倒数' in sentence or '最后' in sentence:
                index = -index
            if index > 0:
                self.choice = self.result_list[index - 1]
            else:
                self.choice = self.result_list[index]
            return True

        pattern = re.compile('[第|最后]([一二三四五12345])')
        m = pattern.search(sentence)
        if m:
            index = trans_number(m.group(1))
            if index > len(self.result_list):
                return False
            if '倒数' in sentence or '最后' in sentence:
                index = -index
            if index > 0:
                self.choice = self.result_list[index - 1]
            else:
                self.choice = self.result_list[index]
            return True
        else:
            intent = self.nlu.requirement_predict(sentence)
            if intent == 'whatever':
                self.choice = self.result_list[0]
                return True
            else:
                for word in whatever_word:
                    if word in sentence:
                        self.choice = self.result_list[0]
                        return True
                return False

    def extract(self, sentence):
        '''
        extract information from user input
        :param sentence:user input
        :return:[{'type':'','word':''}]
        '''
        print("extract")
        tag = self.nlu.phone_slot_predict(sentence)['entities']
        tag = [item for item in tag if item['type'] != 'brand' or item['word'] in brand_list]
        for word in exp_synonyms:
            if word in sentence:
                tag.append({'type': 'experience', 'word': word})
        for word in func_synonyms:
            if word in sentence:
                tag.append({'type': 'function', 'word': word})
        return tag

    def search(self, slot_value_table):
        '''
        do database search
        :param slot_value_table: {'像素':[(3000,'=')]}
        :return:5 query result,[Query_Class]
        '''
        # 调用这个函数进行数据库查询
        condition = slot_value_table
        result = searchPhone(condition)
        self.result_list = result

        return result[0:5]

    def get_result(self):
        '''
        stringify result
        :return: result list contains result string
        '''
        return_slot = ['name', 'price', 'memory', 'disk', 'size', 'camera_back', 'pixel_back']
        res = []
        result_list = self.result_list
        if self.state == 'confirm_choice':
            result_list = [self.choice]
        for item in result_list:
            temp = {}
            itemDict = item.__dict__
            for key in itemDict:
                if key in return_slot:
                    if type(itemDict[key]) == float:
                        temp[key] = itemDict[key]
                    elif itemDict[key] is not None:
                        temp[key] = itemDict[key]

            res.append(temp)
        return res

    def get_slot_table(self):
        '''
        return current slot table
        :return: slot_table dict,{'slot':'value'}
        '''
        res = {}
        op_dict = {'<=': '小于', '=': '', '>=': '大于', '!=': '不要'}
        for slot in self.slot_value:
            if slot in ['体验要求', '功能要求']:
                continue
            sentence_list = []
            for con in self.slot_value[slot]:
                word = con[0] if con[0] != 'whatever' else '不限'
                sentence_list.append(op_dict[con[1]] + str(word))
            slot = nameToColumn[slot]
            res[slot] = ','.join(sentence_list)

        if '体验要求' in self.slot_value:
            sentence_list = []
            for word in self.slot_value['体验要求']:
                if word[1] != '!=':
                    sentence_list.append(word[0])
            if len(sentence_list) > 0:
                res['experience'] = ','.join(sentence_list)

        if '功能要求' in self.slot_value:
            sentence_list = []
            for word in self.slot_value['功能要求']:
                if word[1] != '!=':
                    sentence_list.append(word[0])
            if len(sentence_list) > 0:
                res['function'] = ','.join(sentence_list)
        return res


if __name__ == '__main__':
    pass
