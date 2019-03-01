from random import choice
import pandas as pd

def get_line_set(file_name):
    with open(file_name, encoding='utf-8') as fin:
        lines = fin.readlines()
        line_set = set()
        for line in lines:
            line = line.strip()
            line = line.lower()
            line_set.add(line)
        return line_set

def replace_pattern(pattern, tag_set, label):
    data_list = []
    for tag in tag_set:
        sentence = pattern
        is_placed = False
        while sentence.find(label)!=-1:
            if is_placed:
                random_tag = choice(list(tag_set))
                sentence = sentence.replace(label, random_tag, 1)
            else:
                sentence = sentence.replace(label, tag, 1)
            is_placed = True
        data_list.append(sentence)
    return data_list

def get_pattern_tag(pattern):
    if pattern.find('brand')!= -1:
        return 'brand'
    if pattern.find('frame')!= -1:
        return 'frame'
    if pattern.find('level')!= -1:
        return 'level'
    return None

def get_data():
    data = pd.DataFrame()
    sentence_list = []
    label_list = []

    pattern_data = pd.read_csv('./data_pattern.csv')
    pattern_list = list(pattern_data['sentence'])
    pattern_label = list(pattern_data['label'])
    brand_set = get_line_set('./Brand.txt')
    frame_set = get_line_set('./Frame.txt')
    level_set = get_line_set('./Level.txt')

    for index, pattern in enumerate(pattern_list):
        if pattern.find('Brand') != -1:
            new_data = replace_pattern(pattern, brand_set, 'Brand')
            sentence_list.extend(new_data)
            label_list.extend([pattern_label[index] for i in range(len(new_data))])
        elif pattern.find('Frame') != -1:
            new_data = replace_pattern(pattern, frame_set, 'Frame')
            sentence_list.extend(new_data)
            label_list.extend([pattern_label[index] for i in range(len(new_data))])
        elif pattern.find('Level') != -1:
            new_data = replace_pattern(pattern, level_set, 'Level')
            sentence_list.extend(new_data)
            label_list.extend([pattern_label[index] for i in range(len(new_data))])
        else:
            sentence_list.append(pattern)
            label_list.append(pattern_label[index])

    data['sentence'] = sentence_list
    data['label'] = label_list
    data.to_csv('requirement_data.csv', index=False)

if __name__ == "__main__":
    get_data()