# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String ,Float
import numpy as np
from sqlalchemy import or_ ,not_, and_
import re

from collections import defaultdict
from staticData import nameToColumn,gameRequirement,cpu_level

Base = declarative_base()
class Phone(Base):
    __tablename__ = 'phoneparam'
    
    index = Column(Integer, primary_key=True)
    cpu = Column(String)
    CPUfreq = Column(Float)
    GPU = Column(String)
    resolution = Column(String)
    price = Column(Float)
    core = Column(Integer)
    battery = Column(Float)
    size = Column(Float)
    ram = Column(Float)
    rom = Column(Float)
    frontca = Column(Float)
    backca = Column(Float)
    name = Column(String)
    canum = Column(String)
    good = Column(String)
    
    def toStr(self,s):
        if type(s) == float:
            return str(int(s))
        if s is None:
            return "无"
        return s.decode('utf8')
        
    
    def __repr__(self):
        name = self.toStr(self.name)
        price = self.toStr(self.price)
        cpu = self.toStr(self.cpu)
        ram = self.toStr(self.ram)
        rom = self.toStr(self.rom)
        size = self.toStr(self.size)
        backca = self.toStr(self.backca)
        return "<Phone(型号=%s, 价格=%s, 屏幕大小=%s英寸, 运行内存=%sGB, 内存大小=%sGB, 像素：%s万)>"%(name,price,size,ram,rom,backca)


engine = create_engine('mysql+mysqlconnector://root@localhost:3306/dialog')
Session  = sessionmaker(engine)


def betterCpu(cpu,requriment):
    if cpu is None:
        return True
    cpu = cpu.decode('utf8').replace(' ','')
    requriment = requriment.replace(' ','')
    level_req = cpu_level[requriment]
    pattern = '.*'.join(requriment.split(' '))
    pattern = r'.*%s.*'%pattern
    for c in cpu_level:
        match = re.search(pattern,cpu)
        if match:
            if cpu_level[c]<=level_req:
                return True
            else:
                return False
    return True


def searchPhone(condition):
    '''
    {'negative': {'品牌': [('华为', '=')]}, '价格': [(3000.0, '>=')]}
    '''
    session = Session()
    res = session.query(Phone)
    
    if '品牌' in condition and condition['品牌'][0][0]!='whatever':
        brandList = []
        for brand in condition['品牌']:
            if brand[1]=='=':
                brandList.append(Phone.name.contains(brand[0]))
        res = res.filter(or_(*brandList))
        for brand in condition['品牌']:
            if brand[1]=='!=':
                res = res.filter(not_(Phone.name.contains(brand[0])))
        
    if '价格' in condition and condition['价格'][0][0]!='whatever':
        for con in condition['价格']:
            if con[1] == '>=':
                res = res.filter(Phone.price>=con[0])
            if con[1] == '=':
                res = res.filter(and_(Phone.price>=con[0]-500,Phone.price<=con[0]+500))
            if con[1] == '<=':
                res = res.filter(Phone.price<=con[0])
    
    if '像素' in condition and condition['像素'][0][0]!='whatever':
        for con in condition['像素']:
            if con[1] == '>=':
                res = res.filter(Phone.backca>=con[0])
            if con[1] == '=':
                res = res.filter(and_(Phone.backca>=con[0]-500,Phone.backca<=con[0]+500))
            if con[1] == '<=':
                res = res.filter(Phone.backca<=con[0])
    
    if '运行内存' in condition and condition['运行内存'][0][0]!='whatever':
        for con in condition['运行内存']:
            if con[1] == '>=':
                res = res.filter(Phone.ram>=con[0])
            if con[1] == '=':
                res = res.filter(Phone.ram==con[0])
            if con[1] == '<=':
                res = res.filter(Phone.ram<=con[0])
    
    if '机身内存' in condition and condition['机身内存'][0][0]!='whatever':
        for con in condition['机身内存']:
            if con[1] == '>=':
                res = res.filter(Phone.rom>=con[0])
            if con[1] == '=':
                res = res.filter(Phone.rom==con[0])
            if con[1] == '<=':
                res = res.filter(Phone.rom<=con[0])
                
    

    if '屏幕大小' in condition and condition['屏幕大小'][0][0]!='whatever':
        for con in condition['屏幕大小']:
            if con[1] == '>=':
                res = res.filter(Phone.size>=con[0])
            if con[1] == '=':
                res = res.filter(Phone.size==con[0])
            if con[1] == '<=':
                res = res.filter(Phone.size<=con[0])
    
    res = res.order_by(Phone.index).all()
    
    if '配置要求' in condition:
        ramRequriment = gameRequirement['ram']
        res = [item for item in res if item.ram is not None and item.ram>=ramRequriment]
        cpuRequriment = gameRequirement['cpu']
        res = [item for item in res if betterCpu(item.cpu,cpuRequriment)]

    if '其他' in condition:
        experience = [con[0] for con in condition['其他']]
        score = defaultdict(lambda :0)
        for item in res:
            for word in experience:
                if item.good is None:
                    continue
                if word in item.good.decode('utf8'):
                    score[item.index]+=1
        res = sorted(res,key = lambda x:score[x.index],reverse=True)[0:10]
        res = sorted(res,key = lambda x:x.index)
    return res








