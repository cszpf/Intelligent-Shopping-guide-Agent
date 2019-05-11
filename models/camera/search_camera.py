# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_camera import  function_attr, func_synonyms, exp_synonyms

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

    def __repr__(self):
        name = self.toStr(self.name)
        price = self.toStr(self.price)
        frame = self.toStr(self.frame)
        level = self.toStr(self.level)
        pixel = self.toStr(self.pixel)

        return "<Camera(型号=%s, 价格=%s元, 有效像素=%s万, 画幅=%s, 级别=%s)>" % (name, price, pixel, frame, level)


engine = create_engine('mysql+mysqlconnector://root:120834+1s@127.0.0.1:3306/label_data?charset=utf8')
Session = sessionmaker(engine)


def search_camera(condition):
    '''
    {'negative': {'品牌': [('华为', '=')]}, '价格': [(3000.0, '>=')]}
    '''
    print(condition)
    session = Session()
    res = session.query(Camera)

    if '品牌' in condition and condition['品牌'][0][0] != 'whatever':
        brandList = []
        for brand in condition['品牌']:
            if brand[1] == '=':
                brandList.append(Camera.brand.contains(brand[0]))
        res = res.filter(or_(*brandList))
        for brand in condition['品牌']:
            if brand[1] == '!=':
                res = res.filter(not_(Camera.brand.contains(brand[0])))

    if '价格' in condition and condition['价格'][0][0] != 'whatever':
        for con in condition['价格']:
            if con[1] == '>=':
                res = res.filter(Camera.price >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Camera.price >= con[0] - 3000, Camera.price <= con[0] + 3000))
            if con[1] == '<=':
                res = res.filter(Camera.price <= con[0])

    if '像素' in condition and condition['像素'][0][0] != 'whatever':
        for con in condition['像素']:
            if con[1] == '>=':
                res = res.filter(Camera.pixel >= con[0])
            if con[1] == '=':
                res = res.filter(and_(Camera.pixel >= con[0] - 500, Camera.pixel <= con[0] + 500))
            if con[1] == '<=':
                res = res.filter(Camera.pixel <= con[0])

    if '画幅' in condition and condition['画幅'][0][0] != 'whatever':
        for con in condition['画幅']:
            if con[0] == '半画幅':
                res = res.filter(Camera.frame != '全画幅')
            else:
                res = res.filter(Camera.frame == con[0])

    equal_label = ['级别', '屏幕', '类型', '快门']
    for label in equal_label:
        if label in condition and condition[label][0][0] != 'whatever':
            for con in condition[label]:
                if con[1] == '=':
                    res = res.filter(Camera.level == con[0])

    res = res.order_by(Camera.index).all()
    print(len(res))
    res_dict = [item.__dict__ for item in res]
    score = defaultdict(lambda: 0)
    if '功能要求' in condition:
        requirement = [con[0] for con in condition['功能要求']]

        for req in requirement:
            attrs = function_attr[func_synonyms[req]]
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


if __name__ == "__main__":
    condition = {'品牌': [('索尼', '=')], '价格': [(10000, '=')]}
    result = search_camera(condition)
    print(result)
