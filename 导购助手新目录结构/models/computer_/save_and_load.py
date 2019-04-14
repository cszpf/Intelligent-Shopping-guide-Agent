# -*- coding: utf-8 -*-

import pickle
import codecs


def load(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)
    
def save(model, filename):
    with open(filename, "wb") as f:
        pickle.dump(model, f)


def read(name):
    return codecs.open(name,'r','utf8')

def write(arr,name):
    file = codecs.open(name,'w','utf8')
    for line in arr:
        if line=='\n':
            file.write(line)
        else:
            file.write(line+'\n')
    file.close()