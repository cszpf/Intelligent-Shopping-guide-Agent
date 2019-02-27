import requests
import warnings
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings('ignore')

debug = False

def getIntent(sentence):
    if debug:
        pass
    r = requests.get('http://127.0.0.1:9999/NLU/get_intend/' + sentence)
    print("getIntent:",sentence)
    print("result:",r.text)
    print()
    res = r.json()
    return res

def getSlotIntent(sentence):
    if debug:
        if '不要' in sentence:
            return 'no_need'
    r = requests.get('http://127.0.0.1:9999/NLU/get_requirement/' + sentence)
    print("getSlotIntent:",sentence)
    print("result:",r.text)
    print()
    res = r.json()
    return res

def getSlot(domain,sentence):
    if domain == 'camera':
        r = requests.get('http://127.0.0.1:9999/NLU/get_slot_camera/' + sentence)
        res = r.json()
        return res
    if domain == 'phone':
        if debug:
            if '2000' in sentence:
                if '低于' in sentence:
                    return {'entities': [{'type': 'price_u', 'word': '2000'}], 'string': '低于2000的'}
                if '左右' in sentence:
                    return {'entities': [{'type': 'price_m', 'word': '2000'}], 'string': '2000左右的'}
                if '以上' in sentence:
                    return {'entities': [{'type': 'price_l', 'word': '2000'}], 'string': '2000以上的'}
        r = requests.get('http://127.0.0.1:9999/NLU/get_slot_phone/' + sentence,timeout=1)
        print("getSlot:",sentence)
        print("result:",r.text)
        print()
        res = r.json()        
        return res
    return None

def getChangeIntent(domain,sentence):
    if domain == 'phone':
        changeableSlot = ['价格','屏幕','内存','像素','拍照','照相']
        posWord = ['贵','高','大','宽','好','清晰']
        negWord = ['便宜','小','低','糟糕','少','差']
        positiveCount = 0
        target = ''
        # 匹配描述目标
        for word in changeableSlot:
            if word in sentence:
                target = word
                break
        # 补充目标
        if target == '':
            if any(w in sentence for w in ['贵','便宜']):
                target = '价格'
            elif any(w in sentence for w in ['清晰','拍照','照相']):
                target = '像素'
            elif any(w in sentence for w in ['高','低']):
                target = '价格?'
            elif any(w in sentence for w in ['大','小']):
                target = '屏幕?'
        
        tooWord = ['太','有点','过于','不够']   
        for word in posWord:
            if word in sentence:
                if all(w+word not in sentence for w in tooWord):
                    positiveCount += 1
                else:
                    positiveCount -= 1       
        for word in negWord:
            if word in sentence:
                if all(w+word not in sentence for w in tooWord):
                    positiveCount -= 1
                else:
                    positiveCount += 1
        
        positive = 0
        if positiveCount>0:
            positive = 1
        elif positiveCount<0:
            positive = -1
        
        if target == '内存':
            sentence = sentence.lower()
            if any(w in sentence for w in ['运行内存','ram']):
                target = '运行内存'
            elif any(w in sentence for w in ['机身内存','rom','硬盘']):
                target = '内存大小'
            else:
                target = '内存?'

        return (target,positive)
        
        
        
        
        
        