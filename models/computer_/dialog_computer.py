import numpy as np
import sys
import os

sys.path.append(os.path.dirname(__file__))
from save_and_load import *
import json
import re
from static_data_computer import necessaryTag, labelToTag, ask_slot, listInfo, nameToColumn, adjustableSlot, \
    whatever_word, yes_word, no_word, func_synonyms, exp_synonyms, function_attr, brand_list
from collections import defaultdict
from search_computer import searchComputer


def split_all(s, target=',.?，。？！!'):
    '''
    split a sentence by target
    :param s: input sentence
    :param target: target string
    :return:a list of string
    '''
    sent = []
    line = ''
    for word in s:
        if word not in target:
            line += word
        else:
            sent.append(line)
            line = ''
    if line != '':
        sent.append(line)
    return sent

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


def trans_price(s):
    valide_char = '1234567890一二三四五六七八九十百千万'
    for char in s:
        if char not in valide_char:
            return -1
    if re.match(r'^\d+$', s):
        return int(s)
    digit_char = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
    for i, digit in enumerate(digit_char):
        s = s.replace(digit, str(i + 1))
    s = s.replace('两', str(2))
    match = re.match(r'^[\d+\.*\d*万]*[\d+千]*[\d+百]*[\d+十]*[\d+]*$', s)
    if match:
        base = {'万': 10000, '千': 1000, '百': 100, '十': 10}
        total = 0
        cache = ''
        for digit in s:
            if digit not in base:
                cache += digit
            else:
                total += float(cache) * base[digit]
                cache = ''
        if cache != '':
            total += float(cache)
        return total
    return -1


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
    changeable_slot = ['价格', '硬盘', '内存']
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


p1 = re.compile(r'(i[3|5|7|9][-| ]*\d+[u|m|h|k|q]*)')
p2 = re.compile(r'(i[3|5|7|9])')
cpu_p = [p1, p2]


def extract_cpu(s):
    cpu_set = set()
    for p in cpu_p:
        match = re.findall(p, s)
        for cpu in match:
            cpu_set.add(cpu)
        if len(match) > 0:
            break
    res = []
    for cpu in cpu_set:
        cpu = cpu.replace('-', ' ')
        res.append({'type': 'cpu', 'word': cpu})
    return res


class Computer_Dialogue():
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
        self.morewhat = m['morewhat']
        self.asked = m['asked']
        if self.state == 'result':
            res = self.search(self.slot_value)
            self.result_list = res

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
        targetWord = ['价格']
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
            self.finish = True
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
                self.finish = True
                return

    def result(self, sentence):
        '''
        check user's reponse to the result
        :param sentence:user input
        :return:None
        '''
        if self.check_choice(sentence):
            self.change_state('done')
            self.finish = True
            return
        tag = self.extract(sentence)
        intent = self.nlu.requirement_predict(sentence)
        print(sentence, intent)
        print(tag)
        if len(tag) > 0:
            tag = self.nlu.confirm_slot(tag, sentence)
            to_add = self.fill_message(tag)
            self.write(to_add)
            return
        morewhat = get_change_intent('computer', sentence)
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
            if self.ask_slot != '':
                return get_random_sentence(ask_slot[self.ask_slot])
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
            return get_random_sentence(sentence_list)

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
        bi_tag = ['brand', 'experience', 'function', 'cpu']
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
        print("fill message result:")
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
        # 1. 通过第几个的方式来选择
        if len(self.result_list) == 0:
            return False
        pattern = re.compile('^([一二三四五12345])$')
        m = pattern.search(sentence)
        if (m):
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

    def slot_validate_check(self, sv_pair):
        filtered_sv = []
        number = re.compile(r'^\d+$')
        for sv in sv_pair:
            # check brand
            if sv['type'] == 'brand':
                if sv['word'] not in brand_list:
                    continue
            # check memory
            if 'memory' in sv['type']:
                memory = sv['word']
                memory = memory.lower().replace('gb', '').replace('g', '')
                if not re.match(number, memory):
                    continue
            # check price
            if 'price' in sv['type']:
                price = trans_price(sv['word'])
                if price == -1:
                    continue
                sv['word'] = str(price)
            # check disk
            if 'disk' in sv['type']:
                disk = sv['word']
                disk = disk.lower().replace('gb', '').replace('g', '')
                if not re.match(number, disk):
                    continue
            filtered_sv.append(sv)
        return filtered_sv

    def extract(self, sentence):
        '''
        extract information from user input
        :param sentence:user input
        :return:[{'type':'','word':''}]
        '''
        print("extract")
        sents = split_all(sentence)
        tag = []
        for sent in sents:
            tag.extend(self.nlu.phone_slot_predict(sent)['entities'])
        for word in exp_synonyms:
            if word in sentence:
                tag.append({'type': 'experience', 'word': word})
        func_words = set()
        for word in func_synonyms:
            if word in sentence:
                func_words.add(func_synonyms[word])
        for word in func_words:
            tag.append({'type': 'function', 'word': word})
        cpus = extract_cpu(sentence)
        tag.extend(cpus)
        tag = self.slot_validate_check(tag)
        return tag

    def search(self, slot_value_table):
        '''
        do database search
        :param slot_value_table: {'像素':[(3000,'=')]}
        :return:5 query result,[Query_Class]
        '''
        # 调用这个函数进行数据库查询
        condition = slot_value_table
        result = searchComputer(condition)
        self.result_list = result

        return result[0:5]

    def get_result(self):
        '''
        stringify result
        :return: result list contains result string
        '''
        return_slot = ['name', 'price', 'memory', 'disk', 'cpu_name', 'gpu_name']
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
