# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_computer import nameToColumn, gameRequirement, cpu_level

Base = declarative_base()


class Computer(Base):
    __tablename__ = 'computer_param'

    index = Column(Integer, primary_key=True)
    cpu = Column(String)
    gpu = Column(String)
    price = Column(Float)
    memory = Column(Float)
    disk = Column(Float)
    brand = Column(String)
    name = Column(String)

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


engine = create_engine('mysql+mysqlconnector://root@localhost:3306/dialog')
Session = sessionmaker(engine)


def betterCpu(cpu, requriment):
    if cpu is None:
        return True
    cpu = cpu.decode('utf8').replace(' ', '')
    requriment = requriment.replace(' ', '')
    level_req = cpu_level[requriment]
    pattern = '.*'.join(requriment.split(' '))
    pattern = r'.*%s.*' % pattern
    for c in cpu_level:
        match = re.search(pattern, cpu)
        if match:
            if cpu_level[c] <= level_req:
                return True
            else:
                return False
    return True


def searchComputer(condition):
    '''
    {'negative': {'品牌': [('华为', '=')]}, '价格': [(3000.0, '>=')]}
    '''
    session = Session()
    res = session.query(Computer)

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
                res = res.filter(and_(Computer.price >= con[0] - 1000, Phone.price <= con[0] + 1000))
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


    res = res.order_by(Computer.index).all()

    if '配置要求' in condition:
        ramRequriment = gameRequirement['memory']
        res = [item for item in res if item.ram is not None and item.ram >= ramRequriment]
        cpuRequriment = gameRequirement['cpu']
        res = [item for item in res if betterCpu(item.cpu, cpuRequriment)]

    if '其他' in condition:
        experience = [con[0] for con in condition['其他']]
        score = defaultdict(lambda: 0)
        for item in res:
            for word in experience:
                if item.good is None:
                    continue
                if word in item.good:
                    score[item.index] += 1
        res = sorted(res, key=lambda x: score[x.index], reverse=True)[0:10]
        res = sorted(res, key=lambda x: x.index)
    return res
