# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import numpy as np
from sqlalchemy import or_, not_, and_
import re

from collections import defaultdict
from static_data_camera import nameToColumn

Base = declarative_base()


class Camera(Base):
    __tablename__ = 'camera_param'

    index = Column(Integer, primary_key=True)
    price = Column(Float)
    brand = Column(String)
    level = Column(String)
    pixel = Column(Float)
    name = Column(String)
    frame = Column(String)

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


engine = create_engine('mysql+mysqlconnector://root@localhost:3306/dialog')
Session = sessionmaker(engine)


def search_camera(condition):
    '''
    {'negative': {'品牌': [('华为', '=')]}, '价格': [(3000.0, '>=')]}
    '''
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
            if con[1] == '>=':
                res = res.filter(Camera.frame >= con[0])
            if con[1] == '=':
                res = res.filter(Camera.frame == con[0])
            if con[1] == '<=':
                res = res.filter(Camera.frame <= con[0])
            
    if '级别' in condition and condition['级别'][0][0] != 'whatever':
        for con in condition['级别']:
            if con[1] == '>=':
                res = res.filter(Camera.level >= con[0])
            if con[1] == '=':
                res = res.filter(Camera.level == con[0])
            if con[1] == '<=':
                res = res.filter(Camera.level <= con[0])

    res = res.order_by(Camera.index).all()
    return res 


if __name__ == "__main__":
    condition = {'品牌': [('索尼', '=')], '价格': [(10000, '=')]}
    result = search_camera(condition)
    print(result)
