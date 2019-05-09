# -*- coding: utf-8 -*-
from collections import defaultdict
import numpy as np
import pickle
from scipy.sparse import csr_matrix
from tqdm import tqdm
import re

import sys
import os
sys.path.append(os.path.dirname(__file__))
from save_and_load import *

class index_word():
    def __init__(self):
        self.word_to_index = {}
        self.index_to_word = {}
        self.word_count = 0
        self.word_count_dict = {}
        self.mask = None
    
    def addWord(self,word):
        '''
        输入一个词语
        将其添加到词典中
        '''
        if word in self.word_to_index:
            self.word_count_dict[word] += 1
        else:
            self.word_to_index[word] = self.word_count
            self.index_to_word[self.word_count] = word
            self.word_count_dict[word] = 1
            self.word_count += 1
          
    def buildFromWordDict(self,word_dict):
        '''
        从一个现有的词典中构建
        输入的字典格式：
        {
        word:index
        }
        这种构建没有词频信息
        '''
        self.word_to_index = word_dict
        self.index_to_word = {}
        for word in word_dict:
            self.index_to_word[word_dict[word]] = word
        self.word_count = len(self.word_to_index)
        
    def buildMatrix(self,corpus):
        '''
        输入的是文本list,需要已经分词
        根据已经构建的词频记录来构建
        输出一个csr稀疏矩阵
        '''
        result = []
        index_corpus = [[self.word_to_index[word] for word in line if word in self.word_to_index] for line in corpus]
        #self.index_corpus = index_corpus
        data = []
        col = []
        row = []
        for i in tqdm(range(len(index_corpus))):
            line = index_corpus[i]
            for word in line:
                row.append(i)
                col.append(word)
                data.append(1)        
        # 使用这种方式构建的矩阵，如果再同一个位置有两个值，那么就会加起来，所以不需要统计每个文档的词频
        return csr_matrix((data,(row,col)),shape=(len(corpus),self.word_count))
                
    def buildMatrixS(self,corpus):
        '''
        输入的是文本list,需要已经分词
        根据已经构建的词频记录来构建
        输出一个csr稀疏矩阵
        静默模式
        '''
        result = []
        index_corpus = [[self.word_to_index[word] for word in line if word in self.word_to_index] for line in corpus]
        #self.index_corpus = index_corpus
        data = []
        col = []
        row = []
        for i in range(len(index_corpus)):
            line = index_corpus[i]
            for word in line:
                row.append(i)
                col.append(word)
                data.append(1)        
        # 使用这种方式构建的矩阵，如果再同一个位置有两个值，那么就会加起来，所以不需要统计每个文档的词频
        return csr_matrix((data,(row,col)),shape=(len(corpus),self.word_count))    
        
        
    def addSentence(self,sent):
        for word in sent:
            self.addWord(word)
            
    def indexToWord(self,index):
        w = self.index_to_word[index] if index in self.index_to_word else ''
        return w
    
    def wordToIndex(self,word):
        miss_word = -1
        if '<unk>' in self.word_to_index:
            miss_word = self.word_to_index['<unk>']
        i = self.word_to_index[word] if word in self.word_to_index else miss_word
        return i
    
    def getSize(self):
        return self.word_count
    
    def sentenceToSpecialWord(self,sent):
        '''
        输入为一个句子，会将special word替换成特殊的词语
        输出为替换了special word的句子
        '''
        if self.mask is None:
            self.mask = readList('./data/user_dict.txt')
            mask_dict = {}
            for i in range(len(self.mask)):
                mask_dict['word%d'%i] = self.mask[i]
            self.mask = mask_dict
        for pt in self.mask:
            sent = re.sub(re.escape(self.mask[pt]),pt+' ',sent)
        return sent
    
    def reverseSpecialWord(self,word):
        '''
        输入为一个词语，如果是特殊词语就还原，如果不是特殊词语就原样返回
        '''
        if word in self.mask:
            return self.mask[word]
        else:
            return word
        
    
    def load(self,filename):
        with open(filename, "rb") as f:
            model = pickle.load(f)
            self.word_to_index = model['index']
            self.index_to_word = {}
            for k,v in self.word_to_index.items():
                self.index_to_word[v]=k
            self.word_count = len(self.index_to_word)
            self.word_count_dict = model['count']

    def save(self, filename):
        with open(filename, "wb") as f:
            model = {'index':self.word_to_index,'count':self.word_count_dict}
            pickle.dump(model, f)
