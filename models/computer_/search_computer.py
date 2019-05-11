# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_computer import nameToColumn, cpu_level, gpu_level, function_attr,func_synonyms

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

    def __repr__(self):
        name = self.toStr(self.name)
        price = self.toStr(self.price)
        cpu = self.toStr(self.cpu)
        memory = self.toStr(self.memory)
        disk = self.toStr(self.disk)
        gpu = self.toStr(self.gpu)
        return "<Computer(型号=%s, 价格=%s, cpu=%s, 内存=%sGB, 硬盘=%sGB, gpu：%s)>" % (name, price, cpu, memory, disk, gpu)


engine = create_engine('mysql+mysqlconnector://root:120834+1s@127.0.0.1:3306/dialog?charset=utf8')
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


def searchComputer(condition):
    session = Session()
    res = session.query(Computer)
    print(condition)
    if '品牌' in condition and condition['品牌'][0][0] != 'whatever':
        brandList = []
        for brand in condition['品牌']:
            if brand[1] == '=':
                brandList.append(Computer.name.contains(brand[0]))
        res = res.filter(or_(*brandList))
        for brand in condition['品牌']:
            if brand[1] == '!=':
                res = res.filter(not_(Computer.name.contains(brand[0])))

    if '价格' in condition and condition['价格'][0][0] != 'whatever':
        for con in condition['价格']:
            if con[1] == '>=':
                res = res.filter(Computer.price >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Computer.price >= con[0] - 1000, Computer.price <= con[0] + 1000))
            if con[1] == '<=':
                res = res.filter(Computer.price <= con[0])

    if '内存' in condition and condition['内存'][0][0] != 'whatever':
        for con in condition['内存']:
            if con[1] == '>=':
                res = res.filter(Computer.memory >= con[0])
            if con[1] == '=':
                res = res.filter(Computer.memory == con[0])
            if con[1] == '<=':
                res = res.filter(Computer.memory <= con[0])

    if '硬盘' in condition and condition['硬盘'][0][0] != 'whatever':
        for con in condition['硬盘']:
            if con[1] == '>=':
                res = res.filter(Computer.disk >= con[0])
            if con[1] == '=':
                res = res.filter(Computer.disk == con[0])
            if con[1] == '<=':
                res = res.filter(Computer.disk <= con[0])

    if '处理器' in condition and condition['处理器'][0][0] != 'whatever':
        for con in condition['处理器']:
            if con[1] == '>=':
                res = res.filter(Computer.cpu.contains(con[0]))


    res = res.order_by(Computer.index).all()
    score = defaultdict(lambda: 0)
    if '功能要求' in condition:
        checker_dict = {'cpu': better_cpu, 'gpu': better_gpu, 'memory': better_memory}
        for func in condition['功能要求']:
            attr_requirement = function_attr[func_synonyms[func[0]]]
            for attr in attr_requirement:
                checker = checker_dict[attr]
                for item in res:
                    if (checker(item, attr_requirement[attr])):
                        score[item.index] += 1
                    else:
                        score[item.index] -= 1

    if '体验要求' in condition:
        experience = [con[0] for con in condition['体验要求']]
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
    pass