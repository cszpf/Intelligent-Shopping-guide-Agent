# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_phone import cpu_level, function_attr, func_synonyms, exp_synonyms

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
from mysql_config import mysql_user, mysql_pw

Base = declarative_base()


class Phone(Base):
    __tablename__ = 'phone_param'

    index = Column(Integer, primary_key=True)
    id = Column(Integer)
    cpu = Column(String)
    price = Column(Float)
    size = Column(Float)
    disk = Column(Float)
    memory = Column(Float)
    pixel_front = Column(Float)
    pixel_back = Column(Float)
    camera_front = Column(String)
    camera_back = Column(String)
    name = Column(String)
    brand = Column(String)
    tags = Column(String)

    def toStr(self, s):
        if type(s) == float:
            return str(int(s))
        if s is None:
            return "无"
        return s

    def convert_bytes_to_str(self):
        self.cpu = self.cpu.decode('utf8') if type(self.cpu) == bytes else self.cpu
        self.camera_front = self.camera_front.decode('utf8') if type(self.camera_front) == bytes else self.camera_front
        self.camera_back = self.camera_back.decode('utf8') if type(self.camera_back) == bytes else self.camera_back
        self.name = self.name.decode('utf8') if type(self.name) == bytes else self.name
        self.brand = self.brand.decode('utf8') if type(self.brand) == bytes else self.brand
        self.tags = self.tags.decode('utf8') if type(self.tags) == bytes else self.tags

    def __repr__(self):
        name = self.toStr(self.name)
        price = self.toStr(self.price)
        cpu = self.toStr(self.cpu)
        memory = self.toStr(self.memory)
        disk = self.toStr(self.disk)
        size = self.toStr(self.size)
        camera_back = self.toStr(self.camera_back)
        return "<Phone(型号=%s, 价格=%s, 屏幕大小=%s英寸, 运行内存=%sGB, 内存大小=%sGB, 像素：%s万)>" % (
            name, price, size, memory, disk, camera_back)


engine = create_engine('mysql+mysqlconnector://%s:%s@127.0.0.1:3306/dialog?charset=utf8' % (mysql_user, mysql_pw))
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


def searchPhone(condition):
    '''
    {'negative': {'品牌': [('华为', '=')]}, '价格': [(3000.0, '>=')]}
    '''
    session = Session()
    res = session.query(Phone)
    print("search:", condition)
    if 'brand' in condition and condition['brand'][0][0] != 'whatever':
        brandList = []
        for brand in condition['brand']:
            if brand[1] == '=':
                brandList.append(Phone.brand.contains(brand[0]))
        res = res.filter(or_(*brandList))
        for brand in condition['brand']:
            if brand[1] == '!=':
                res = res.filter(not_(Phone.brand.contains(brand[0])))

    if 'price' in condition and condition['price'][0][0] != 'whatever':
        for con in condition['price']:
            if con[1] == '>=':
                res = res.filter(Phone.price >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Phone.price >= con[0] - 500, Phone.price <= con[0] + 500))
            if con[1] == '<=':
                res = res.filter(Phone.price <= con[0])

    if 'pixelb' in condition and condition['pixelb'][0][0] != 'whatever':
        for con in condition['pixelb']:
            if con[1] == '>=':
                res = res.filter(Phone.pixel_back >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Phone.pixel_back >= con[0] - 500, Phone.pixel_back <= con[0] + 500))
            if con[1] == '<=':
                res = res.filter(Phone.pixel_back <= con[0])

    if 'memory' in condition and condition['memory'][0][0] != 'whatever':
        for con in condition['memory']:
            if con[1] == '>=':
                res = res.filter(Phone.memory >= con[0])
            if con[1] == '=':
                res = res.filter(Phone.memory == con[0])
            if con[1] == '<=':
                res = res.filter(Phone.memory <= con[0])

    if 'disk' in condition and condition['disk'][0][0] != 'whatever':
        for con in condition['disk']:
            if con[1] == '>=':
                res = res.filter(Phone.disk >= con[0])
            if con[1] == '=':
                res = res.filter(Phone.disk == con[0])
            if con[1] == '<=':
                res = res.filter(Phone.disk <= con[0])

    if 'size' in condition and condition['size'][0][0] != 'whatever':
        for con in condition['size']:
            if con[1] == '>=':
                res = res.filter(Phone.size >= con[0])
            if con[1] == '=':
                res = res.filter(Phone.size == con[0])
            if con[1] == '<=':
                res = res.filter(Phone.size <= con[0])

    res = res.order_by(Phone.index).all()
    for item in res:
        item.convert_bytes_to_str()
    score = defaultdict(lambda: 0)
    if 'function' in condition:
        checker_dict = {'cpu': better_cpu, 'memory': better_memory}
        for func in condition['function']:
            name = func_synonyms[func[0]]
            if name not in function_attr:
                continue
            attr_requirement = function_attr[name]
            for attr in attr_requirement:
                checker = checker_dict[attr]
                for item in res:
                    if checker(item, attr_requirement[attr]):
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
