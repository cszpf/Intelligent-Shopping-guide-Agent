# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_camera import function_attr, func_synonyms, exp_synonyms

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
from mysql_config import mysql_user, mysql_pw

Base = declarative_base()


class Camera(Base):
    __tablename__ = 'camera_param'

    index = Column(Integer, primary_key=True)
    id = Column(Integer)
    price = Column(Float)
    brand = Column(String)
    level = Column(String)
    pixel = Column(Float)
    name = Column(String)
    frame = Column(String)
    type = Column(String)
    screen = Column(String)
    shutter = Column(String)

    def toStr(self, s):
        if type(s) == float:
            return str(int(s))
        if s is None:
            return "无"
        return s

    def convert_bytes_to_str(self):
        self.brand = self.brand.decode('utf8') if type(self.brand) == bytes else self.brand
        self.level = self.level.decode('utf8') if type(self.level) == bytes else self.level
        self.name = self.name.decode('utf8') if type(self.name) == bytes else self.name
        self.frame = self.frame.decode('utf8') if type(self.frame) == bytes else self.frame
        self.type = self.type.decode('utf8') if type(self.type) == bytes else self.type
        self.screen = self.screen.decode('utf8') if type(self.screen) == bytes else self.screen
        self.shutter = self.shutter.decode('utf8') if type(self.shutter) == bytes else self.shutter

    def __repr__(self):
        name = self.toStr(self.name)
        price = self.toStr(self.price)
        frame = self.toStr(self.frame)
        level = self.toStr(self.level)
        pixel = self.toStr(self.pixel)

        return "<Camera(型号=%s, 价格=%s元, 有效像素=%s万, 画幅=%s, 级别=%s)>" % (name, price, pixel, frame, level)


engine = create_engine('mysql+mysqlconnector://%s:%s@127.0.0.1:3306/dialog?charset=utf8' % (mysql_user, mysql_pw))
Session = sessionmaker(engine)


def convert_bytes_to_str(res):
    result = []
    for item in res:
        for key in item:
            if type(item[key]) == bytes:
                item[key] = item[key].decode('uitf8')
        result.append(item)
    return result


def search_camera(condition):
    '''
    {'negative': {'品牌': [('华为', '=')]}, '价格': [(3000.0, '>=')]}
    '''
    print("search:", condition)
    session = Session()
    res = session.query(Camera)

    if 'brand' in condition and condition['brand'][0][0] != 'whatever':
        brandList = []
        for brand in condition['brand']:
            if brand[1] == '=':
                brandList.append(Camera.brand.contains(brand[0]))
        res = res.filter(or_(*brandList))
        for brand in condition['brand']:
            if brand[1] == '!=':
                res = res.filter(not_(Camera.brand.contains(brand[0])))

    if 'price' in condition and condition['price'][0][0] != 'whatever':
        for con in condition['price']:
            if con[1] == '>=':
                res = res.filter(Camera.price >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Camera.price >= con[0] - 3000, Camera.price <= con[0] + 3000))
            if con[1] == '<=':
                res = res.filter(Camera.price <= con[0])

    if 'pixel' in condition and condition['pixel'][0][0] != 'whatever':
        for con in condition['pixel']:
            if con[1] == '>=':
                res = res.filter(Camera.pixel >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Camera.pixel >= con[0] - 500, Camera.pixel <= con[0] + 500))
            if con[1] == '<=':
                res = res.filter(Camera.pixel <= con[0])

    if 'frame' in condition and condition['frame'][0][0] != 'whatever':
        for con in condition['frame']:
            if con[0] == '半画幅':
                res = res.filter(Camera.frame != '全画幅')
            else:
                res = res.filter(Camera.frame == con[0])

    res = res.order_by(Camera.index).all()
    for item in res:
        item.convert_bytes_to_str()
    res_dict = [item.__dict__ for item in res]
    res_dict = [item for item in res_dict if item is not None]
    score = defaultdict(lambda: 0)
    equal_label = ['level', 'screen', 'type', 'shutter']
    for label in equal_label:
        if label in condition and condition[label][0][0] != 'whatever':
            for con in condition[label]:
                if con[1] == '=':
                    for item in res_dict:
                        if item[label] is None:
                            continue
                        if con[0] in item[label]:
                            score[item['index']] += 1

    if 'function' in condition:
        requirement = [func_synonyms[con[0]] for con in condition['function']]

        for req in requirement:
            name = func_synonyms[req]
            if name not in function_attr:
                continue
            attrs = function_attr[name]
            for attr in attrs:
                if attr == 'price':
                    if ',' in attrs[attr]:
                        lower, upper = attrs[attr].split(',')
                        lower = int(lower)
                        upper = int(upper)
                        for item in res:
                            if item.price >= lower and item.price <= upper:
                                score[item.index] += 1
                    else:
                        lower = int(attrs[attr])
                        for item in res:
                            if item.price >= lower:
                                score[item.index] += 1
                else:
                    for item in res_dict:
                        for term in attrs[attr]:
                            if term == item[attr]:
                                score[item['index']] += 1

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


if __name__ == "__main__":
    condition = {'level': [['入门级', '=']], 'brand': [['佳能', '=']], 'price': [[5000.0, '=']], 'type': [['微单', '=']], 'frame': [['whatever', '=']]}
    result = search_camera(condition)
    print(result)
