# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_computer import cpu_level, gpu_level, function_attr,func_synonyms

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
from mysql_config import mysql_user,mysql_pw

Base = declarative_base()


class Computer(Base):
    __tablename__ = 'computer_param'

    index = Column(Integer, primary_key=True)
    id = Column(Integer)
    cpu = Column(String)
    cpu_name = Column(String)
    gpu = Column(String)
    gpu_name = Column(String)
    price = Column(Float)
    memory = Column(Float)
    disk = Column(Float)
    brand = Column(String)
    name = Column(String)
    tags = Column(String)

    score = 0

    def get_score(self):
        return self.score

    def add_score(self, s=1):
        self.score += s

    def toStr(self, s):
        if type(s) == float:
            return str(int(s))
        if s is None:
            return "无"
        return s.decode('utf8')
    
    def convert_bytes_to_str(self):
        self.cpu = self.cpu.decode('utf8') if type(self.cpu) == bytes else self.cpu 
        self.cpu_name = self.cpu_name.decode('utf8') if type(self.cpu_name) == bytes else self.cpu_name 
        self.gpu = self.gpu.decode('utf8') if type(self.gpu) == bytes else self.gpu 
        self.gpu_name = self.gpu_name.decode('utf8') if type(self.gpu_name) == bytes else self.gpu_name 
        self.brand = self.brand.decode('utf8') if type(self.brand) == bytes else self.brand 
        self.name = self.name.decode('utf8') if type(self.name) == bytes else self.name 
        self.tags = self.tags.decode('utf8') if type(self.tags) == bytes else self.tags 

    def __repr__(self):
        name = self.toStr(self.name)
        price = self.toStr(self.price)
        cpu = self.toStr(self.cpu)
        memory = self.toStr(self.memory)
        disk = self.toStr(self.disk)
        gpu = self.toStr(self.gpu)
        return "<Computer(型号=%s, 价格=%s, cpu=%s, 内存=%sGB, 硬盘=%sGB, gpu：%s)>" % (name, price, cpu, memory, disk, gpu)


engine = create_engine('mysql+mysqlconnector://%s:%s@127.0.0.1:3306/dialog?charset=utf8'%(mysql_user,mysql_pw))
Session = sessionmaker(engine)


def better_cpu(item, requriment):
    if item.cpu is None:
        return False
    if item.cpu in cpu_level and requriment in cpu_level:
        l1 = cpu_level[item.cpu]
        l2 = cpu_level[requriment]
        print(item.cpu, l1)
        print(requriment, l2)
        if l1 <= l2:
            return True
    return False


def better_gpu(item, requriment):
    if item.gpu is None:
        return False
    if item.gpu in gpu_level and requriment in gpu_level:
        l1 = gpu_level[item.gpu]
        l2 = gpu_level[requriment]
        print(item.gpu, l1)
        print(requriment, l2)
        if l1 <= l2:
            return True
    return False


def better_memory(item, requriment):
    if item.memory is None:
        return False
    m1 = item.memory
    m2 = requriment.replace('GB', '')
    m2 = int(m2)
    if m1 >= m2:
        return True
    else:
        return False

def convert_bytes_to_str(res):
    result = []
    for item in res:
        for key in item:
            if type(item[key]) == bytes:
                item[key] = item[key].decode('uitf8')
        result.append(item)
    return result


def searchComputer(condition):
    session = Session()
    res = session.query(Computer)
    print("search",condition)
    if 'brand' in condition and condition['brand'][0][0] != 'whatever':
        brandList = []
        for brand in condition['brand']:
            if brand[1] == '=':
                brandList.append(Computer.name.contains(brand[0]))
        res = res.filter(or_(*brandList))
        for brand in condition['brand']:
            if brand[1] == '!=':
                res = res.filter(not_(Computer.name.contains(brand[0])))

    if 'price' in condition and condition['price'][0][0] != 'whatever':
        for con in condition['price']:
            if con[1] == '>=':
                res = res.filter(Computer.price >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Computer.price >= con[0] - 1000, Computer.price <= con[0] + 1000))
            if con[1] == '<=':
                res = res.filter(Computer.price <= con[0])
            if con[1] == '<':
                res = res.filter(Computer.price < con[0])
            if con[1] == '>':
                res = res.filter(Computer.price > con[0])

    if 'memory' in condition and condition['memory'][0][0] != 'whatever':
        for con in condition['memory']:
            if con[1] == '>=':
                res = res.filter(Computer.memory >= con[0])
            if con[1] == '=':
                res = res.filter(Computer.memory == con[0])
            if con[1] == '<=':
                res = res.filter(Computer.memory <= con[0])
            if con[1] == '<':
                res = res.filter(Computer.memory < con[0])
            if con[1] == '>':
                res = res.filter(Computer.memory > con[0])

    if 'disk' in condition and condition['disk'][0][0] != 'whatever':
        for con in condition['disk']:
            if con[1] == '>=':
                res = res.filter(Computer.disk >= con[0])
            if con[1] == '=':
                res = res.filter(Computer.disk == con[0])
            if con[1] == '<=':
                res = res.filter(Computer.disk <= con[0])
            if con[1] == '<':
                res = res.filter(Computer.disk < con[0])
            if con[1] == '>':
                res = res.filter(Computer.disk > con[0])

    if 'cpu' in condition and condition['cpu'][0][0] != 'whatever':
        for con in condition['cpu']:
            if con[1] == '=':
                res = res.filter(Computer.cpu.contains(con[0]))


    res = res.order_by(Computer.index).all()
    for item in res:
        item.convert_bytes_to_str()
    score = defaultdict(lambda: 0)
    if 'function' in condition:
        checker_dict = {'cpu': better_cpu, 'gpu': better_gpu, 'memory': better_memory}
        for func in condition['function']:
            name = func_synonyms[func[0]]
            if name not in function_attr:
                continue
            attr_requirement = function_attr[name]
            for attr in attr_requirement:
                checker = checker_dict[attr]
                for item in res:
                    if (checker(item, attr_requirement[attr])):
                        score[item.index] += 1
                    else:
                        score[item.index] -= 1

    if 'experience' in condition:
        experience = [con[0] for con in condition['experience']]
        for exp in experience:
            for item in res:
                if item.tags is not None and exp in item.tags:
                    score[item.index] += 1

    res = sorted(res, key=lambda x: score[x.index], reverse=True)
    res_ = []
    last_id = -1
    for item in res:
        if item.id == last_id:
            continue
        else:
            res_.append(item)
            last_id = item.id
    if len(res_) < 5:
        res_id = [item.id for item in res_]
        for item in res:
            if item.id not in res_id:
                res_.append(item)
    return res_

if __name__ == '__main__':
    res = searchComputer({'memory': [[8.0, '>=']], 'brand': [['whatever', '=']], 'function': [['ps', '=']], 'price': [[7000.0, '=']]})
