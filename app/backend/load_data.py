#!/usr/bpandas columnsin/python3.6
# -*- coding: utf-8 -*-  
"""
    本文件用于加载各种数据
"""
import pandas as pd
import json
file_list = ['./data/forum_1',
        './data/forum_2',
        './data/alignment_attrs.json',
        './data/suningComputers.json', 
        './data/京东/笔记本',
        './data/京东/轻薄本',
        './data/京东/台式机',
        './data/京东/一体机'
        ]

def load_data_set(tag):
    """
    param tag: 需要加载的文件
             forum: return list of dataframe [forum_1, forum_2]
             alignment: return dict alignment_attrs
             jingdong: return list of dataframe [笔记本, 轻薄本，台式机，一体机‘】
    """
    if tag == 'forum':
        forum_1 = pd.read_csv(file_list[0])
        forum_2 = pd.read_csv(file_list[1])
        return [forum_1, forum_2]
    elif tag == 'alignment':
        return None
    
    elif tag == 'computer':
        with open(file_list[3]) as f:
            data = json.load(f)
        return data
    elif tag == 'jingdong':
        data_list = []
        for i in range(len(file_list)):
            if i < 4:
                continue
            file_name = file_list[i].split('/')[-1]
            data = pd.read_csv(file_list[i])

            data_list.append(data)
        return data_list
    return None


def load_text_file(data_path, flags = 0):
    """
    flags: 0:一行一个字符串，按行读取（默认）
    :param data_path:
    :return: list
    """
    if flags == 0:
        result = list()
        with open(data_path) as f:
            line = f.readline()
            while line:
                result.append(line.strip())
                line = f.readline()
        return result


if __name__ == '__main__':
   # test
   data = load_data_set('forum')
   print(type(data))
   for d in data:
       print(d.columns)
       print(d.head())
       print(len(d))
       print()
   data2 = load_data_set('alignment')
   print(type(data2))
   data3 = load_data_set('computer')
   print(data3)
   data4 = load_data_set('jingdong')
   print(data4)
